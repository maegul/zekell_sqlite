
from pathlib import Path
from typing import Optional, Iterable
import sqlite3 as sql
from dataclasses import dataclass
from pprint import pprint


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

    db.ex('''
        create table if not exists
        notes (
            id integer primary key,
            title text,
            metadata text,
            body text,
            mod_time text
        )
        ''')

    # FTS virtual table
    db.ex('''
        create virtual table if not exists
        notes_fts using fts5(
            title,
            body,
            content='notes',
            content_rowid='id'
        )
        ''')

    # triggers to sync notes with FTS table

    db.ex('''
        create trigger if not exists
        notes_ai
        after insert on notes
        begin
            insert into notes_fts (rowid, title, body)
                values (new.id, new.title, new.body);
        end
        ''')

    db.ex('''
        create trigger if not exists
        notes_ad
        after delete on notes
        begin
            insert into notes_fts(notes_fts, rowid, title, body)
                values('delete', old.id, old.title, old.body);
        end
        ''')

    db.ex('''
        create trigger if not exists
        notes_au
        after update on notes
        begin
            insert into notes_fts(notes_fts, rowid, title, body)
                values('delete', old.id, old.title, old.body);
            insert into notes_fts (rowid, title, body)
                values (new.id, new.title, new.body);
        end
        ''')


def create_note_links_table(db: DB):

    db.ex("""
        create table if not exists
        note_links (
            id interger primary key,
            parent_note_id integer,
            child_note_id integer,
            foreign key (parent_note_id)
                references notes (id),
            foreign key (child_note_id)
                references notes (id)
        )
        """)


def create_tags_table(db: DB):

    query = """
        create table if not exists
        tags (
            id integer primary key autoincrement,
            tag text,
            parent_id text,
            foreign key (parent_id) references tags (id),
            unique (
                tag, parent_id
                )
            on conflict abort
        )
    """

    output = db.ex(query)

    print(output)



def create_note_tags_table():
    ...


# > Add functions

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




