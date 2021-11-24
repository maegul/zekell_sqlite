#! /usr/bin/env python3

from pprint import pprint
import subprocess as sp
import string
from textwrap import dedent
from argparse import ArgumentParser
import datetime as dt
import copy
import json
from string import Template
from pathlib import Path
import re
import subprocess
# 3.5+ then!
from typing import Optional, Iterable, Tuple, Union, overload
import sqlite3 as sql

# when package, needs to be managed
# SCHEMA_PATH = Path('./schema.sql')
SCHEMA_PATH = Path(__file__).parent / Path('./schema.sql')

# > Config

default_config = {
    "zk_paths": {
        "main": "~/zekell"
    },
    "current_zk_path": "main",
    "note_extension": ".md",
    # "editor_shell_command": "vim, {}"
    "editor_shell_command": "subl, -n, {}"
}

default_config_path = Path('~/.zekell_config').expanduser()

def write_default_config(output_path: Path = default_config_path):

    output_path.touch(exist_ok=True)
    output_path.write_text(
        json.dumps(default_config))

def get_config():
    if not default_config_path.exists():
        return default_config
    else:
        base_config = copy.deepcopy(default_config)

        base_config.update(
            json.loads(
                default_config_path.read_text()))

        return base_config

config = get_config()

# >> Set global consts from config

# MAIN ONE IS ZK_PATH ... how to deal with path depends on how this library is called
# probably best to contextualise the path at calling before passing note_path variables
# down to functions

NOTE_EXTENSION = config['note_extension']
ZK_PATH = Path(config['zk_paths'][config['current_zk_path']]).expanduser()
ZK_DB = Path('zekell.db')
ZK_DB_PATH = ZK_PATH / ZK_DB

# > Objects & Consts

note_name_template = Template('$id $title').substitute
note_file_name_template = Template('$id $title'+NOTE_EXTENSION).substitute

note_name_pattern = re.compile(r'^(\d{10,14}) (.*)')
# make link_pattern more permissive so that title/comment can be anything?
link_pattern = re.compile(r'\[(.*?)\]\(\/(\d{10,14})\)')
# non greedy for contents so that don't accidentally match whole file!
front_matter_pattern = re.compile(r'(?s)^---\n(.+?)\n---')

# links to notes to be created on parsing ... add later ... nice to have
# Must have a title (at least one character) and no id, but a slash!
# new_link_pattern = re.compile(r'\[([\w\- ]+)\]\(\/\)')


class DB:

    def __init__(self, conn: sql.Connection, cursor: sql.Cursor):
        self.conn = conn
        self.cursor = cursor

    def ex(
            self, query: Union[str, list, tuple],
            params: Optional[Union[list, tuple]] = None):
        """Execute query and return fetchall and commit

        If query is a list (of queries/statements), then they will be run as a batch
        with `commit` being run only after all have been executed.

        Passing params along with a list of queries/statements requires params to be
        a list/tuple of lists/tuples, with the inner lists/tuples containing the params
        for each query.

        If params are None, no params are used for a list of queries
        If one of the elements in the outer list of params is None, then no params are used
        for the corresponding query

        Examples
        --------
        >>> db.ex('select * from notes')
        >>> db.ex('select * from notes where id = ?', [123])
        >>> db.ex('select * from note_links where parent_id = ? and child_id = ?', [123, 789])
        >>> db.ex(
            [
            'select * from notes',
            'select * from notes where id = ? or id = ?'],
            [
            None,
            [123, 456]
            ]
        )
        """

        if isinstance(query, (list, tuple)):
            # check that arguments appropriate for batch operation
            if not (
                    (
                        isinstance(params, (list, tuple))
                        and
                        all(
                            isinstance(
                                p, (list, tuple, type(None)))
                            for p in params
                            )
                        and
                        (len(query) == len(params))
                    )
                    or
                    isinstance(query, (list, tuple))
                    ):
                raise ValueError(
                    '''If running batch, query must be list of queries and,
                    if provided, params a list of lists of parameters,
                    with the outer list with the same length as the query list'''
                    )
            else:
                if params is None:
                    params = [None for _ in query]
                with self.conn:  # auto commit/rollback
                    for q, p in zip(query, params):
                        if p:
                            self.cursor.execute(q, p)
                        else:
                            self.cursor.execute(q)

                    output = self.cursor.fetchall()

        else:  # if not batch
            with self.conn:  # auto commit/rollback
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)

                output = self.cursor.fetchall()


        return output


class NoteName:

    def __init__(self, id: int, title: Optional[str] = None):
        self.id = id
        self._title = title

    @property
    def title(self):
        return '' if not self._title else self._title

class Note:
    def __init__(
            self,
            name: NoteName,
            frontmatter: Optional[str] = None,
            body: Optional[str] = None,
            tags: Optional[list] = None,
            links: Optional[list] = None
            ):

        self.name = name
        self.id = name.id
        self.title = name.title
        self.frontmatter = frontmatter
        self.body = body
        self.tags: list = [] if tags is None else tags
        self.links: list = [] if links is None else links


class NoteError(ValueError):
    pass

# > Table Creation

def db_connection(db_path: Path, new: bool = False) -> DB:

    if not db_path.exists() and not new:
        raise ValueError('Db Path exists already!')
    elif new:
        db_path.touch()

    conn = sql.connect(db_path)
    cursor = conn.cursor()
    db = DB(conn, cursor)

    # foreign keys on and check
    db.cursor.execute('pragma foreign_keys = ON')
    db.cursor.execute('pragma foreign_keys;')
    fk_check = db.cursor.fetchone()
    if fk_check[0] != 1:
        raise sql.DatabaseError('Foreign Keys not enabled')

    return db


def db_init(db: DB):
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()

    db.cursor.executescript(schema)

##############
# PREVIOUS CREATION CODE DEPRECATED WITH INIT
##############




# > Add to Tables

# >> Notes

def make_mod_time() -> float:
    "timestamp of right now in UTC (for recording modified times)"
    return dt.datetime.utcnow().timestamp()

def get_note_mod_time(note_path: Path) -> float:
    "modified time of a file, according to OS, as timestamp, in UTC time"
    file_mtime = note_path.stat().st_mtime
    # file_mtime is in system/OS timezone
    # utcfromtimestamp gives time in UTC timezone
    return dt.datetime.utcfromtimestamp(file_mtime).timestamp()

def make_new_note_id() -> int:
    now = int(dt.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    return now


def make_note_name_string(note_name: NoteName) -> str:

    return '{id} {title}'.format(
        id = note_name.id,
        title = '' if not note_name.title else note_name.title
        )


def make_note_file_name(note_name: NoteName) -> str:

    return '{note_name}{ext}'.format(
        note_name = make_note_name_string(note_name),
        ext = NOTE_EXTENSION)


def parse_note_name(source: Union[str, Path]) -> NoteName:

    if isinstance(source, Path):
        source_string = source.stem

    else:
        source_string = source

    note_name = note_name_pattern.search(source_string)
    if not note_name:
        raise NoteError(
            'Note file name ({}) not valid for note found at {}'
            .format(source)
            )

    note_id = int(note_name.group(1))
    note_title: str = note_name.group(2)

    return NoteName(id=note_id, title=note_title)


def is_note_id_unique(db: DB, note_id: int) -> bool:
    # this could probably done faster?
    # perhaps a try-except on an insert would be fastest, to rely on sqlite's internals
    # but, not sure how to accurately catch a unique constraint problem
    # as they're not exposed (until oct 2021) by python API
    # BEST approach may be to only to this when necessary ... after a try-except
    output = db.ex('select count(*) from notes where id = ?', [note_id])

    return output[0][0] == 0


def make_unique_new_note_id(db: DB):
    "Check that unique and increment up to 5 times until unique if necessary"

    new_id = make_new_note_id()

    # try to ensure unique by waiting for id to be unique
    if not is_note_id_unique(db, new_id):
        for _ in range(5):  # retry for 5 seconds
            new_id += 1
            if is_note_id_unique(db, new_id):
                break
        else:  # if no break
            raise NoteError(
                'Could not generate unique id for new note (last try: {})'.format(new_id))

    return new_id


def make_batch_new_note_ids(db: DB, n: int) -> list:
    "Make multiple new note ids by incrementing by one n times"

    base_id = make_unique_new_note_id(db)
    new_ids = [base_id + i for i in range(1, n+1)]

    return new_ids


# >> Links


def add_note_link(db: DB, parent_id: int, child_id: int):
    """Add link between parent and child

    Unique constraint errors are skipped with "insert or ignore"
    Foreign key constraint is not ignored/skipped
    """

    insert_stmt = (
        '''
        insert or ignore
        into note_links(parent_note_id, child_note_id)
        values(?, ?)''',
        [parent_id, child_id]
        )

    try:
        db.ex(*insert_stmt)
    # presuming to be a foreign key constrant (as unique is ignored)
    except sql.IntegrityError as _:
        raise NoteError('Child note with id ({}), cited in {}, does not exist'.format(
            child_id, parent_id))


def update_note_links(
        db: DB, parent_id: int,
        child_ids: Union[int, list, tuple]):


    # rewrite db.ex to not do batch but instead have a flag for whether to commit
    # that way, can manually hold multiple queries until the end, then commit
    # should be more flexible

    # or not ...

    delete_stmt = '''delete from note_links where parent_note_id = ?'''
    insert_stmt = '''
        insert or ignore
        into note_links(parent_note_id, child_note_id)
        values(?, ?)'''

    if isinstance(child_ids, (list, tuple)):
        db.ex(
            query = [
                delete_stmt,
                *[insert_stmt for _ in child_ids]],
            params = [
                [parent_id],
                *[(parent_id, child_id) for child_id in child_ids] ]
            )
    else:
        db.ex(
            query=[
                delete_stmt,
                insert_stmt],
            params = [
                [parent_id],
                [parent_id, child_ids]]
            )


# >> Tags

def check_root_tag_unique(db: DB, tag_name: str):

    query = """
    select * from tags where tag = ? and parent_id IS NULL
    """

    output = db.ex(query, [tag_name])

    if output:
        raise sql.IntegrityError('Root tag not unique')



tag_path_pattern = re.compile(r'[a-zA-Z_][a-zA-Z_\/]*[a-zA-Z_]')

def is_valid_tag_path(tag_path: str):
    return tag_path_pattern.fullmatch(tag_path)

def check_valid_tag_path(tag_path: str):
    if not is_valid_tag_path(tag_path):
        raise NoteError('tag path ({}) is not valid (must fullmatch with {})'.format(
            tag_path, tag_path_pattern.pattern))


def get_tag_id(db: DB, tag: str, parent_id: Optional[int]) -> int:

    # sqlite: "is" works with null, "=" doesn't
    result = db.ex(
        'select id from tags where tag = ? and parent_id is ?',
        [tag, parent_id]
        )

    return result[0][0]


def get_tag_path_id(db: DB, tag_path: str) -> int:
    check_valid_tag_path(tag_path)

    result = db.ex(
        'select id from full_tag_paths where full_tag_path = ?',
        [tag_path])

    return result[0][0]


def get_all_full_tag_path(db: DB) -> list:
    paths = [
        tp[0] for tp
        in db.ex('select full_tag_path from full_tag_paths')
    ]

    return paths


def add_tag(
    db: DB, tag: str,
    parent_id: Optional[int] = None):

    # Manually check that root tag is unique
    # necessary as NULL (parent of root tags) is always unique
    if not parent_id:
        check_root_tag_unique(db, tag)

    query = """
    insert into tags(tag, parent_id)
    values(?, ?)
    """

    db.ex(query, [tag, parent_id])


def add_new_tag_path(db: DB, new_tag_path: str):
    """Add tags necessary for new_tag_path to refer to an extant tag

    return None if necessary tags already exist
    return id of newly created tag (leaf) if new tag(s) created
    """

    check_valid_tag_path(new_tag_path)

    paths = get_all_full_tag_path(db)

    new_path_parents = [  # get longest match from all tag_paths
        tag_path for tag_path
        in paths
        if tag_path in new_tag_path
        ]

    if new_tag_path in paths:
        # shouldn't happen, but just in case
        return

    new_path_parent = max(new_path_parents, default=None)

    # no match or match does not start from beginning or is not SUB-string (ie too long)
    # then new path is all new tags
    if not new_path_parent or not (new_tag_path.find(new_path_parent) == 0):
        new_path_parent_id = None
        # whole path is new!
        new_tags = new_tag_path.split('/')
    else:
        new_path_parent_id = get_tag_path_id(db, new_path_parent)
        # get list of new tags that need to be added with new_path_parent at root
        new_tags = new_tag_path[len(new_path_parent)+1:].split('/')

    for new_tag in new_tags:
        add_tag(db, new_tag, parent_id = new_path_parent_id)
        new_id = get_tag_id(db, new_tag, parent_id=new_path_parent_id)
        # now use new tag as parent id for the next
        new_path_parent_id = new_id

    # return id of new tag

    return new_id  # type: ignore


def add_note_tag(db, note_id: int, tag_id: int):

    db.ex('''
        insert into note_tags(note_id, tag_id) values(?,?)''',
        [note_id, tag_id]
        )


def update_note_tags(db, note_id: int, tag_ids: Union[int, list, tuple]):


    delete_stmt = '''delete from note_tags where note_id = ?'''
    insert_stmt = '''
        insert into note_tags(note_id, tag_id)
        values(?, ?)'''

    if isinstance(tag_ids, (list, tuple)):
        db.ex(
            query = [
                delete_stmt,
                *[insert_stmt for _ in tag_ids]],
            params = [
                [note_id],
                *[(note_id, tag_id) for tag_id in tag_ids]]
            )
    else:
        db.ex(
            query = [
                delete_stmt,
                insert_stmt],
            params = [
                [note_id],
                [note_id, tag_ids]]
            )



# >> Parsing notes


def parse_note_body(body: str) -> Tuple[str, list, list]:
    """Returns frontmatter, tags and links

    tags is list of strings of full_tag_path
    links is list of note_ids (str)
    """

    # parse front matter
    front_matter = front_matter_pattern.match(body)

    # unsure if notes need frontmatter ... at the moment ... no
    # if not front_matter:
    #     raise NoteError('Note contains no valid front matter')

    metadata = {}
    front_matter_text = ''
    if front_matter:
        front_matter_text = front_matter.group(1)
        for line in front_matter_text.splitlines():
            key, value = [token.strip() for token in line.split(':')]

            if key == 'tags':
                # ensure no repeat tags ... convert back to list for cleanness downstream
                tags = list(
                    set([token.strip() for token in value.split(',')])
                    )
                for tag in tags:
                    # catch invalid tags early
                    check_valid_tag_path(tag)
                metadata[key] = tags
            else:
                metadata[key] = value


    # parse links
    links = link_pattern.findall(body)
    # convert set back to list for cleanness downstream
    link_ids = list(set(link[1] for link in links))

    tags = metadata.get('tags', [])

    return front_matter_text, tags, link_ids


def parse_note(note_path: Path) -> Note:
    """Read and parse text of a note to get all necessary data
    """

    note_name = parse_note_name(note_path)

    with open(note_path) as f:
        body = f.read()

    front_matter_text, tags, link_ids = parse_note_body(body)

    note = Note(
        name = note_name,
        frontmatter=front_matter_text,
        body=body,
        tags=tags,
        links=link_ids
        )

    return note


def stage_note(db: DB, note_path: Path):
    "Add a note to the staging table"

    note_name = parse_note_name(note_path)

    db.ex('insert or ignore into staged_notes(id, title, note_path, add_time) values(?,?,?,?)',
        [note_name.id, note_name.title, note_path.as_posix(), make_mod_time()])


def make_new_note(db: DB, title: Optional[str] = None):
    """Create a new note with ID formed by current time and provided title

    Content intended to be added by another function.  This is for initialisation
    """

    # get id
    new_id = make_new_note_id()

    # use try block to check uniqueness of id as sqlite check is prob better than manual query
    try:
        db.ex('insert into notes(id, title) values(?, ?)', [new_id, title])
    except sql.IntegrityError:
        new_id = make_unique_new_note_id(db)
        db.ex('insert into notes(id, title) values(?, ?)', [new_id, title])

    note_name = NoteName(new_id, title)
    note_path = (ZK_PATH / Path(make_note_file_name(note_name)))
    note_path.touch(exist_ok=False)

    # add entry in staged table
    stage_note(db, note_path)
    # db.ex('insert into staged_notes(id, title, note_path, add_time) values(?,?,?,?)',
    #     [note_name.id, note_name.title, note_path.as_posix(), make_mod_time()])


    return note_path


def update_note(db: DB, note_path: Path):
    "Update content of existing note"
    # everything but the ID (that would be a new note)
    # tags could be tricky ... probably need a separate add/update tags function

    if not note_path.exists():
        raise NoteError('Note not found at path {}'.format(source))

    note = parse_note(note_path)

    db.ex('''
        update notes
        set
            title = ?,
            frontmatter = ?,
            body = ?,
            mod_time = ?
        where id = ?''',
        [note.title, note.frontmatter, note.body, make_mod_time(), note.id]
        )

    update_note_links(db, note.id, note.links)

    # Tags
    # can roll up into a generalised update function?
    # or good to keep tag update function simple and leave management here ... ?
    tag_paths = get_all_full_tag_path(db)
    new_tag_paths = []
    for tag_path in note.tags:
        check_valid_tag_path(tag_path)
        if tag_path in tag_paths:
            tag_id = get_tag_path_id(db, tag_path)
        else:
            tag_id = add_new_tag_path(db, tag_path)
            if tag_id is None:
                raise NoteError('Failed to add new tag ({})'.format(tag_path))

        new_tag_paths.append(tag_id)
        # add_note_tag(db, note.id, tag_id)
    update_note_tags(db, note.id, new_tag_paths)

    # remove from staging
    db.ex('delete from staged_notes where id = ?', [note.id])


def add_old_note(db, note_path: Path):

    note = parse_note(note_path)

    if not is_note_id_unique(db, note.id):
        raise NoteError('old note id {} is not unique (note_path: {})'.format(
            note.id, note_path))

    db.ex('insert into notes(id, title) values(?, ?)', [note.id, note.title])
    update_note(db, note_path)

    # BIG ISSUE Here with note_links and the foreign key constraint
    # if adding notes one at a time, a link is likely to be to a note not yet added
    # and can be unresolvable adding only one note at a time
    # BETTER to batch add all the notes into the notes table only, then update
    # keep a list of failed notes to report at the end


def add_batch_old_note(db, note_paths: list):

    failed_notes = set()
    for note_path in note_paths:
        note = parse_note(note_path)

        if not is_note_id_unique(db, note.id):
            raise NoteError('old note id {} is not unique (note_path: {})'.format(
                note.id, note_path))

        try:
            db.ex('insert into notes(id, title) values(?, ?)', [note.id, note.title])
        except Exception:
            failed_notes.add(note_path)

    update_fails = set()
    for note_path in note_paths:
        if note_path not in failed_notes:
            try:
                update_note(db, note_path)
            except Exception:
                update_fails.add(note_path)

    return failed_notes, update_fails


def update_all_notes(db: DB, note_dir_path: Path) -> Tuple[set, set]:
    "Add or update all note_path files in note_dir_path"

    note_paths = note_dir_path.glob(f'*{NOTE_EXTENSION}')

    new_note_paths = []
    update_note_paths = []

    for note_path in note_paths:
        note = parse_note(note_path)
        result = db.ex('select mod_time from notes where id = ?', [note.id])
        # note not in database as empty list returned
        if not result:
            new_note_paths.append(note_path)
        else:
            mod_time = float(result[0][0])
            note_mod_time = get_note_mod_time(note_path)
            # note file modified since database entry was last updated
            if note_mod_time > mod_time:
                update_note_paths.append(note_path)

    # add new notes
    failed, update_failed = add_batch_old_note(db, new_note_paths)

    # update notes that have been modified
    for note_path in update_note_paths:
        try:
            update_note(db, note_path)
        except Exception:
            update_failed.add(note_path)

    return failed, update_failed


def delete_note(db: DB, note_path: Path):
    "delete note from db and file"


    # note_name = parse_note_name(note_path)
    note = parse_note(note_path)
    db.ex(
        [
            'delete from notes where id = ?',
            'delete from note_links where parent_note_id = ?',
            'delete from note_tags where note_id = ?'
        ],
        [
            [note.id],
            [note.id],
            [note.id]
        ]
        )

    note_path.unlink()


# >> Staging and Opening Notes

def open_note(db: DB, note_path: Path):
    open_note_command = [
        element.strip()
        for element in
            config['editor_shell_command']
            .format(note_path)
            .split(',')
        ]

    _ = subprocess.call(open_note_command)

    stage_note(db, note_path)




# > query notes

# >> Fuzzy id

def get_note_ids_from_fuzzy_id(db: DB, fuzzy_id: int) -> Optional[Union[list, Path]]:

    note_cands = db.ex('select id, title from notes where id like ("%" || ?)', [fuzzy_id])

    if not note_cands:
        return
    elif len(note_cands) > 1:
        return note_cands
    else:
        note_path = ZK_PATH / Path(make_note_file_name(NoteName(*note_cands[0])))
        return note_path

# >> CTEs

def id_cte(note_id: int):
    "CTE for selecting notes by tail of note_id"

    id_cte = f'''
    id_notes(note_id) as (
        select id from notes
        where id like "%{note_id}"
    )
    '''
    return dedent(id_cte)

def tag_cte(tag: str):
    "CTE for select note_ids with a single tag"

    tag_cte = f'''
    tagged_notes(note_id) as (
        select note_id from note_tags
        where tag_id = (
            select id from full_tag_paths where full_tag_path = "{tag}"
        )
    )
    '''

    return dedent(tag_cte)

def title_cte(phrase: str):
    '''
    CTE for selecting note_ids of all notes with matching FTS phrase in title

    phrase formats include:
    "token1 token2" (implicit AND)
    "token1 + token2" (single search term ... concatenated into single)
    "(token1 AND token2) OR token3" (booleans with operators in caps and parens for order)
    '''

    title_cte = f'''
    title_notes(note_id) as (
        select rowid from notes_fts
        where title match "{phrase}"
    )
    '''
    return dedent(title_cte)

def body_cte(phrase: str):
    '''
    CTE for selecting note_ids of all notes with matching FTS phrase in body

    phrase formats include:
    "token1 token2" (implicit AND)
    "token1 + token2" (single search term ... concatenated into single)
    "(token1 AND token2) OR token3" (booleans with operators in caps and parens for order)
    '''

    body_cte = f'''
    body_notes(note_id) as (
        select rowid from notes_fts
        where body match "{phrase}"
    )
    '''
    return dedent(body_cte)

def child_cte(note_id: int):
    "CTE for all notes that are child of note_id"

    child_cte = f'''
    child_notes(note_id) as (
        select child_note_id from note_links
        where parent_note_id = "{note_id}"
    )
    '''
    return dedent(child_cte)

def children_cte(*_):
    """all children of all previously selected notes

    Is a passive follow-through CTE that simply allows for a join
    """

    cte = f'''
    children_notes(parent_note_id, note_id) as (
        select parent_note_id, child_note_id
        from note_links
    )
    '''

    return dedent(cte)

def parents_cte(*_):
    """all children of all previously selected notes

    Is a passive follow-through CTE that simply allows for a join
    """

    cte = f'''
    parents_notes(note_id, child_note_id) as (
        select parent_note_id, child_note_id
        from note_links
    )
    '''

    return dedent(cte)

def tag_or_cte(tags: str):
    "CTE for all notes with any or all of tags provided as 'a, b, c'"

    tags_tuple = tuple(t.strip() for t in tags.split(','))
    cte = f'''
    tagged_or_notes(note_id) as (
        select note_id
        from note_tags
        where tag_id in (
            select id from full_tag_paths where full_tag_path in {tags_tuple}
        )
        group by note_id
    )
    '''
    return dedent(cte)

def tag_and_cte(tags: str):
    "CTE for all notes with all of the provided tags provided as 'a b c' (implicit AND)"

    tags_tuple = tuple(t.strip() for t in tags.split(' '))
    cte = f'''
    tagged_and_notes(note_id) as (
        select note_id
        from note_tags
        where tag_id in (
            select id from full_tag_paths where full_tag_path in {tags_tuple}
        )
        group by note_id
        having count(note_id) = {len(tags_tuple)}
    )
    '''
    return dedent(cte)

# >> CTE keywords to functions maping

# just single characters from alphabet ... could maybe create a mapping
cte_aliases = list(string.ascii_lowercase)

cte_map = {
    'id': id_cte,
    'title': title_cte,
    'body': body_cte,
    'child': child_cte,
    'children': children_cte,
    'parents': parents_cte,
    'tag': tag_cte,
    'tag_or': tag_or_cte,
    'tag_and': tag_and_cte
}
# name of CTE defined by cte function (mapped from keywords above)
cte_table_name_map = {
    'id': 'id_notes',
    'title': 'title_notes',
    'body': 'body_notes',
    'child': 'child_notes',
    'children': 'children_notes',
    'parents': 'parents_notes',
    'tag': 'tagged_notes',
    'tag_or': 'tagged_or_notes',
    'tag_and': 'tagged_and_notes'
}

# >>> CTE join constraints

# join constraint for ordinary note_id-on-note_id CTEs
# all have a basic note_id on note_id join as all the filtering occurs WITHIN the CTE
cte_ordinary_join_constraint = "on {left}.note_id = {right}.note_id".format

cte_join_constraints = {
    'id': cte_ordinary_join_constraint,
    'title': cte_ordinary_join_constraint,
    'body': cte_ordinary_join_constraint,
    'child': cte_ordinary_join_constraint,
    'tag': cte_ordinary_join_constraint,
    'tag_or': cte_ordinary_join_constraint,
    'tag_and': cte_ordinary_join_constraint,
    # flow-through CTE, must join on distinct column and pass new note_id column through
    'children': "on {left}.note_id = {right}.parent_note_id".format,
    'parents': "on {left}.note_id = {right}.child_note_id".format
}


def query_tag_redirect(parsed_q: dict):
    "Alter which tag cte used according to contents of query"

    tag_query = parsed_q.get('tag')
    if tag_query is None:  # no need for redirect, no tag component
        return parsed_q

    if tag_query.find(',') != -1:  # first, as spaces found with commas
        parsed_q['tag_or'] = parsed_q['tag']
        del parsed_q['tag']
    elif tag_query.find(' ') != -1:
        parsed_q['tag_and'] = parsed_q['tag']
        del parsed_q['tag']

    return parsed_q


# >> Full query

def mk_super_query(q: str, notes_cols: Optional[list] = None):
    '''
    Take string (q) and generate sql query

    Format of q is: "key-word: query; ..."

    See cte_map for key-words and associated cte functions for possible args

    Works by having each cte create a note_id column for their selection, and inner joining
    each of these CTEs on the note_id columns.
    Finally, the main selection is made on the notes table and joined onto the final CTE
    '''

    # parse q into keywords and associated queries
    parsed_q = {}
    for sq in q.split(';'):
        # use partition for when no args provided with command
        # partition returns an empty string when no separator
        ssq = sq.strip().partition(':')
        parsed_q[ssq[0].strip()] = ssq[2].strip()

    # alter tag keyword as appropriate for contents of the query
    parsed_q = query_tag_redirect(parsed_q)

    # create CTEs by concatenating and starting with "with"
    sq = 'with' + ','.join(cte_map[k](v) for k,v in parsed_q.items())

    # add main initial select cols statement, using notes_cols if provided
    # select from alias "z", as this is hardcoded below to be the notes table
    if not notes_cols:
        notes_cols = ['id', 'title']
    #                                     V this "z" is alias for notes table (below)
    selection_cols = f"select {','.join(f'z.{col}' for col in notes_cols)}\n"
    sq += selection_cols

    # add join statements with aliases from the alphabet
    for i, k in enumerate(parsed_q.keys()):
        alias = cte_aliases[i]
        prev_alias = cte_aliases[i-1]
        if i == 0:
            sq += f"from {cte_table_name_map[k]} {alias}"
        else:
            sq += dedent(
                    f"""
                    inner join {cte_table_name_map[k]} {alias}
                    {cte_join_constraints[k](left=prev_alias, right=alias)}"""
                        )

    # add final join on notes table
    sq += f"\ninner join notes z on {alias}.note_id = z.id"  # type: ignore

    return sq

# > Fancy Functions

# apply tag to all children of current note


# > CLI

def display_rows(db: DB, result: list):

    print(' | '.join([c[0] for c in db.cursor.description]))
    for row in result:
        print(' | '.join([str(v) for v in row]))


def cli_config(args):

    if args.print:
        pprint(config)
        print('Config file at {} exists: {}'.format(
            default_config_path, default_config_path.exists()))

    if args.init:
        write_default_config()
        print('Written config file to {}'.format(default_config_path))


def cli_init(args):

    db_path = ZK_PATH/ZK_DB

    if args.print:
        print('Zekell initialised at {} with DataBase: {}'.format(
                ZK_PATH, (ZK_PATH.exists(), db_path.exists())
            ))
        if db_path.exists():
            print('Database path: {}'.format(db_path))

    else:
        if db_path.exists():
            print('Zekell already exists at {}'.format(db_path))
            db = db_connection(db_path)
        else:
            ZK_PATH.mkdir(exist_ok=True)
            db = db_connection(new=True, db_path=db_path)
            print('Created Zekell at {} and Database at {}'.format(
                ZK_PATH, db_path))

        db_init(db)
        print('Zekell Database schema initialised')

        print('\nTables:')
        print(
           '\n'.join([
                r[0] for r in
                db.ex('select name from sqlite_master where type = "table"')
            ])
            )
        print('\nNumber of notes: {}'.format(
            db.ex('select count(*) from notes')[0][0])
        )


def cli_add(args):

    db = db_connection(ZK_DB_PATH)
    note_path = make_new_note(db, args.title)


    print(note_path)

def cli_staged_notes(args):

    db = db_connection(ZK_DB_PATH)

    if not args.update:
        result = db.ex('select id, title from staged_notes order by add_time desc')
        display_rows(db, result)

    elif args.update:
        note_paths = [
            Path(row[0])
            for row in
            db.ex('select note_path from staged_notes')
        ]

        failed_notes = []
        for note_path in note_paths:
            try:
                update_note(db, note_path)
            except Exception:
                failed_notes.append(note_path)

        if failed_notes:
            print('Failed to update:')
            print('\n'.join(failed_notes))


def cli_open(args):

    db = db_connection(ZK_DB_PATH)
    note_results = get_note_ids_from_fuzzy_id(db, args.note_id)

    if not note_results:
        print('No Notes found with id {}'.format(args.note_id))
    elif isinstance(note_results, list):
        print('Multiple candidates found')
        display_rows(db, note_results)
    else:
        open_note(db, note_results)

def cli_update(args):
    db = db_connection(ZK_DB_PATH)

    note_results = get_note_ids_from_fuzzy_id(db, args.note_id)

    if not note_results:
        print('No Notes found with id {}'.format(args.note_id))
    elif isinstance(note_results, list):
        print('Multiple candidates found')
        display_rows(db, note_results)
    else:  # note_results is path
        note_path = note_results

        # if title of note has been changed, presume ID is the same
        if not note_results.exists():
            note = parse_note_name(note_results)
            note_path_candidates = list(ZK_PATH.glob(f'{note.id}*'))
            if not note_path_candidates:
                print('No note files found with id {}'.format(note.id))
            elif len(note_path_candidates) != 1:
                print('Multiple note files found with id {}'.format(note.id))
                print(note_path_candidates)
            else:
                note_path = note_path_candidates[0]

        update_note(db, note_path)


def cli_update_all(_):

    db = db_connection(ZK_DB_PATH)
    failed, update_failed = update_all_notes(db, ZK_PATH)

    # need to start logging this sort of stuff!
    if failed or update_failed:
        print('Failed to add notes:')
        print(failed)
        print('Failed to update notes:')
        print(update_failed)


def cli_query(args):

    query = 'select {} limit {}'.format(args.query, args.limit)
    db = db_connection(ZK_DB_PATH)
    result = db.ex(query)

    display_rows(db, result)

def cli_search(args):

    query = mk_super_query(args.query)
    db = db_connection(ZK_DB_PATH)
    result = db.ex(query)

    display_rows(db, result)

def cli_graph(_):

    db = db_connection(ZK_DB_PATH)
    q = '''
        select a.parent_note_id, b.title, a.child_note_id, c.title
        from note_links a
        left join notes b on a.parent_note_id = b.id
        left join notes c on a.child_note_id = c.id
    '''

    links = db.ex(q)

    all_nodes = set()
    for l in links:
        all_nodes.add((l[0], l[1]))
        all_nodes.add((l[2], l[3]))

    lines = []
    lines.append('digraph test {\n')
    lines.append('rankdir=LR;\n')
    for n in all_nodes:
        lines.append(f'\t{n[0]} [label="{n[1]}"]\n')
    lines.append('\n')
    for l in links:
        lines.append(f'\t{l[0]} ->{l[2]}\n')
    lines.append('}')

    graph_file = ZK_PATH / Path('zk_graph.dot')
    out_file = graph_file.with_suffix('.svg')

    with open(graph_file, 'w') as f:
        f.writelines(lines)

    _ = sp.check_output(
            ['dot', '-Tsvg', graph_file.as_posix(), '-o', out_file.as_posix()]
        )

    _ = sp.check_output(['open', '-a', 'Safari', out_file.as_posix()])

def main():
    parser = ArgumentParser(
        description="Zekell CLI"
        )

    subparsers = parser.add_subparsers(
        dest='sub_command', title='Sub Commands')

    # >> Config

    ap_config = subparsers.add_parser('config', description='Configuration',
        help='View or manage configuration')
    ap_config.add_argument('-p', '--print',
        action='store_true',
        help="Print current config and setup")
    ap_config.add_argument('--init',
        action='store_true',
        help="Create default config file to allow user customisation")

    # >> Initialisation

    ap_init = subparsers.add_parser('init', description='Initialisation',
        help="Initialise your Zekell")
    ap_init.add_argument('-p', '--print',
        action='store_true',
        help='Print current state for initialisation')

    # >> Locate

    _ = subparsers.add_parser('locate', description='Locate',
        help="Locate current Zekell, print path")

    # >> Add New Note

    ap_add = subparsers.add_parser('add', description='Add New Note',
        help='Add a new note')
    ap_add.add_argument('-t', '--title',
        help="Title of the new note",
        )

    # >> Staged notes
    ap_staged = subparsers.add_parser('staged', description='Staged Notes',
        help='Managed staged notes')
    ap_staged.add_argument('-u', '--update',
        action = 'store_true',
        help='Update all staged notes from file')

    # >> Open Notes
    ap_open = subparsers.add_parser('open', description='Open note in editor',
        help='Open note by note_id in editor in configuration')
    ap_open.add_argument('note_id',
        help='note id to open, can be tail of id which will succeed if possible or print multiples',
        type=int)

    # >> Update Note
    ap_update = subparsers.add_parser('update', description='Update note',
        help='Update note by note_id ')
    ap_update.add_argument('note_id',
        help='note_id of note to update, can be tail which can be tail of full id as with open',
        type=int)

    # >> Update all notes
    ap_update_all = subparsers.add_parser('update-all', description='Update or add all notes',
        help='All notes in zekell path will be added or if modified since last updated, updated')

    # >> Run SQL Query

    ap_query = subparsers.add_parser('sql', description='Run Query',
        help='Run a sql select query against the database')
    ap_query.add_argument('query',
        help='Query to run, will be automatically preceded by "select "')
    ap_query.add_argument('-l', '--limit',
        help='Number to limit return by (default 100)',
        default = 100)

    # >> Run Search Query
    # uses basic custom format
    ap_search = subparsers.add_parser('q', description='Search Notes',
        help='Run a search for notes')
    ap_search.add_argument('query',
        help=f'''
        Query to search with.
        Format: "keyword: query; ...".
        Keywords: {', '.join(cte_map.keys())}''')

    ap_graph = subparsers.add_parser('graph', description='Make graph of zetellkasten',
        help='Use graphviz (dot) to make svg graph and open with Safar'
        )



    args = parser.parse_args()

    if args.sub_command == 'config':
        cli_config(args)
    elif args.sub_command == 'init':
        cli_init(args)
    elif args.sub_command == 'locate':
        if ZK_PATH.exists():
            print(ZK_PATH)
        else:
            print('Zekell not initialised at configured path: {}, try init'.format(
                ZK_PATH))
    elif args.sub_command == 'add':
        cli_add(args)
    elif args.sub_command == 'staged':
        cli_staged_notes(args)
    elif args.sub_command == 'open':
        cli_open(args)
    elif args.sub_command == 'update':
        cli_update(args)
    elif args.sub_command == 'update-all':
        cli_update_all(args)
    elif args.sub_command == 'sql':
        cli_query(args)
    elif args.sub_command == 'q':
        cli_search(args)
    elif args.sub_command == 'graph':
        cli_graph(args)

if __name__ == '__main__':
    main()

