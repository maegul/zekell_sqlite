
from collections import namedtuple
import datetime as dt
from pathlib import Path
import re
from typing import Optional, Iterable
import sqlite3 as sql
from dataclasses import dataclass
from pprint import pprint

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


@dataclass
class DB:
    conn: sql.Connection
    cursor: sql.Cursor

    def ex(self, query: str, params: Optional[Iterable] = None):
        """Execute query and return fetchall and commit"""

        with self.conn:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            output = self.cursor.fetchall()

        return output


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

def check_root_tag_unique(db: DB, tag_name: str):

    query = """
    select * from tags where tag = ? and parent_id IS NULL
    """

    output = db.ex(query, [tag_name])

    if output:
        raise sql.IntegrityError('Root tag not unique')


def add_tag(db: DB, tag_name: str, parent_id: Optional[int] = None):

    # Manually check that root tag is unique
    # necessary as NULL (parent of root tags) is always unique
    if not parent_id:
        check_root_tag_unique(db, tag_name)

    query = """
    insert into tags(tag, parent_id)
    values(?, ?)
    """

    output = db.ex(query, (tag_name, parent_id))
    print(output)


def add_link(db: DB):
    ...


def update_links(db: DB, links):
    # delete all links according to parent of provided links
    # insert all links provided
    ...


def add_note():
    ...


def update_note():
    # incorporate into add_note?
    ...

# > Note Parsing

title_pattern = re.compile(r'^(\d{12,14}) (.*)')
front_matter_pattern = re.compile(r'(?s)^---\n(.+)\n---')
link_pattern = re.compile(r'\[(.*)\]\(\/(\d{12,14})\)')

Note = namedtuple('Note', ['id', 'title', 'frontmatter', 'body', 'tags', 'links'])

class NoteError(ValueError):
    pass

def parse_note(note_path: Path) -> Note:
    """Read and parse text of a note to get all necessary data
    """

    if not note_path.exists():
        raise NoteError('Note not found at path {}'.format(note_path))

    note_name = title_pattern.search(note_path.stem)
    if not note_name:
        raise NoteError('Note file name ({}) not valid for note found at {}'.format(
            note_path.stem, note_path))
    note_id, note_title = note_name.groups()
    with open(note_path) as f:
        body = f.read()

    # parse front matter
    front_matter = front_matter_pattern.match(body)

    if not front_matter:
        raise NoteError('Note contains no valid front matter')

    front_matter_text = front_matter.group(1)
    metadata = {}
    for line in front_matter_text.splitlines():
        key, value = [token.strip() for token in line.split(':')]

        if key == 'tags':
            metadata[key] = [token.strip() for token in value.split(',')]
        else:
            metadata[key] = value

    # will probably remove this and frontmatter exception above
    # so that notes can not have front matter as one grows out of having tags
    if 'tags' not in metadata:
        raise NoteError('No tags found in note at {}'.format(note_path))

    # parse links
    links = link_pattern.findall(body)
    # convert set back to list for cleanness downstream
    link_ids = list(set(link[1] for link in links))

    note = Note(
        id=note_id,
        title=note_title,
        frontmatter=front_matter_text,
        body=body,
        # presumes tags always present!
        tags=metadata['tags'],
        links=link_ids
        )

    return note





# > query notes

# all notes matching any of provided tags

# full text search over title or text or both

# all children of current note

# all 1st deg parents / children

# > Fancy Functions

# apply tag to all children of current note
