import datetime as dt
from string import Template
from pathlib import Path
import re
# 3.5+ then!
from typing import Optional, Iterable, Tuple, Union, overload
import sqlite3 as sql

# when package, needs to be managed
SCHEMA_PATH = Path('./schema.sql')
NOTE_EXTENSION = '.md'

# need to implement some basic config reading here
    # config name: .zekell_config
    # location: home and/or current path (no searching up the tree)
    # options: zk_path, alt_paths, note_extension
    # just use python and importlib?

ZK_PATH = Path('./prototype')

# > Objects & Consts

note_name_template = Template('$id $title').substitute
note_file_name_template = Template('$id $title'+NOTE_EXTENSION).substitute

note_name_pattern = re.compile(r'^(\d{10,14}) (.*)')
link_pattern = re.compile(r'\[([\w\- ]*)\]\(\/(\d{10,14})\)')
front_matter_pattern = re.compile(r'(?s)^---\n(.+)\n---')

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


# ===========
class NoteName:

    def __init__(self, id: int, title: Optional[str] = None):
        self.id = id
        self._title = title

    @property
    def title(self):
        return '' if not self._title else self._title
# -----------

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
        raise ValueError('Db Path does not exist')

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
    return dt.datetime.utcnow().timestamp()


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

        # core data about the file
        if not source.exists():
            raise NoteError('Note not found at path {}'.format(source))

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
                metadata[key] = list(set([token.strip() for token in value.split(',')]))
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
    (ZK_PATH / Path(make_note_file_name(note_name))).touch(exist_ok=False)


def update_note(db: DB, note_path: Path):
    "Update content of existing note"
    # everything but the ID (that would be a new note)
    # tags could be tricky ... probably need a separate add/update tags function

    note = parse_note(note_path)

    db.ex('''
        update notes
        set
            title = ?,
            frontmatter = ?,
            body = ?,
            mod_time = ?
        where id = ? ''',
        [note.title, note.frontmatter, note.body, make_mod_time(), note.id]
        )

    update_note_links(db, note.id, note.links)

    # Tags
    # can roll up into a generalised update function?
    # or good to keep tag update function simple and leave management here ... ?
    for tag_path in note.tags:
        check_valid_tag_path(tag_path)
        tag_paths = get_all_full_tag_path(db)
        if tag_path in tag_paths:
            tag_id = get_tag_path_id(db, tag_path)
        else:
            tag_id = add_new_tag_path(db, tag_path)
            if tag_id is None:
                raise NoteError('Failed to add new tag ({})'.format(tag_path))

        add_note_tag(db, note.id, tag_id)




def delete_note(db: DB, note_path: Path):
    "delete note from db and file"


    note_name = parse_note_name(note_path)
    db.ex('''
        delete from notes
        where id = ? ''', [note_name.id])

    note_path.unlink()



# >> Links


def update_links(db: DB, links):
    # delete all links according to parent of provided links
    # insert all links provided
    ...








# > query notes

# all notes matching any of provided tags

# full text search over title or text or both

# all children of current note

# all 1st deg parents / children

# > Fancy Functions

# apply tag to all children of current note
