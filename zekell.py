
from typing import Optional
from pathlib import Path
import sqlite3 as sql
from dataclasses import dataclass
from pprint import pprint


# > Objects
@dataclass
class DB:
    conn: sql.Connection
    cursor: sql.Cursor

    def ex(self, query: str):
        """Execute query and return fetchall and commit"""

        with self.conn:
            self.cursor.execute(query)
            output = self.cursor.fetchall()

        return output


# > Functions

# >> Table Creation

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


def create_notes_table(db: DB):
    ...


def create_tags_table(db: DB):

    query = """
        create table if not exists
        tags (
            id integer primary key autoincrement,
            tag text,
            parent_id text,
            foreign key (parent_id) references tags (id)
        )
    """
    output = db.ex(query)

    print(output)


def create_note_tags_table():
    ...


def create_note_links_table():
    ...



# > Testing
# ===========
# db_path = Path('test.db')
# db = db_connection(db_path, True)
# # -----------
# # ===========
# create_tags_table(db)
# # -----------
# # ===========
# pprint(db.ex("select * from sqlite_master where type='table'"))
# # -----------
# # ===========
# db_path.unlink()
# # -----------
