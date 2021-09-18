
from pathlib import Path
from typing import Optional, Iterable
import sqlite3 as sql
from dataclasses import dataclass
from pprint import pprint

SCHEMA_PATH = Path('./schema.sql')

# > Objects


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


def create_tag_paths_table_trigger(db: DB):

    # trigger to create full tag path table on each insert, delete, update
    ...


def create_note_tags_table():
    ...


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
    if not parent_id:
        check_root_tag_unique(db, tag_name)

    query = """
    insert into tags(tag, parent_id)
    values(?, ?)
    """

    output = db.ex(query, (tag_name, parent_id))
    print(output)




