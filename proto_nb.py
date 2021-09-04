# ===========
from zekell import *
# -----------

# > Testing
# ===========
db.conn.close()
# -----------
# ===========
db_path = Path('test.db')
db = db_connection(db_path, True)
# # -----------
# >> Files table with FTS
# ===========
create_notes_table(db)
# -----------



# cols: id, title, metadata, body, m-date
# ===========
import datetime as dt
# -----------
# ===========
dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')
# -----------
# ===========

# -----------
# ===========
db.ex('''
    create table notes (
        id integer primary key,
        title text,
        metadata text,
        body text,
        mod_time text
    )
    ''')
# -----------
# ===========
db.ex('''
    insert into notes
    values(?, ?, ?, ?, ?)
    ''',
    (
        int(dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')),
        'My first note',
        '''---
        title: My first note
        tags: first, demo
        ---''',
        '''This is a demo note

        Not much more to day''',
        dt.datetime.utcnow().timestamp()

        ))
# -----------
# ===========
db.ex('select * from notes')
# -----------
# ===========
db.ex('''
    create virtual table notes_fts using fts5(
        title,
        body,
        content='notes',
        content_rowid='id'
    )
    ''')
# -----------
# ===========
db.ex('select * from notes_fts')
# -----------
# ===========
# shouldn't work yet ... not FTS content
db.ex("select * from notes_fts where notes_fts match 'demo'")
# -----------
# ===========
# create triggers
# ... slightly different for FTS with special notes_fts column and 'delete' values
db.ex('''
    create trigger if not exists notes_ai
    after insert on notes
    begin
        insert into notes_fts (rowid, title, body)
            values (new.id, new.title, new.body);
    end''')
db.ex('''
    create trigger if not exists notes_ad
    after delete on notes
    begin
        insert into notes_fts(notes_fts, rowid, title, body)
            values('delete', old.id, old.title, old.body);
    end
    ''')
db.ex('''
    create trigger if not exists notes_au
    after update on notes
    begin
        insert into notes_fts(notes_fts, rowid, title, body)
            values('delete', old.id, old.title, old.body);
        insert into notes_fts (rowid, title, body)
            values (new.id, new.title, new.body);
    end
    ''')
# -----------
# ===========
db.ex('''
    insert into notes
    values(?, ?, ?, ?, ?)
    ''',
    (
        int(dt.datetime.utcnow().timestamp()),
        'My second note',
        '''---
        title: My second note
        tags: second, demo
        ---''',
        '''This is another demo note

        Not much more to day''',
        dt.datetime.utcnow().timestamp()

        ))
# -----------
# ===========
db.ex('select * from notes_fts')
# -----------
# ===========
db.ex("select * from notes_fts where notes_fts match 'demo'")
# -----------
# ===========
db.ex("select rowid,* from notes_fts where notes_fts match 'demo'")
# -----------
# ===========
db.ex("delete from notes")
# -----------
# ===========
db.ex("delete from notes where id = 20210829110444")
# -----------
# ===========
db.ex("select rowid,* from notes_fts where notes_fts match 'demo'")
# -----------
# playing with FTS queries
# ===========
db.ex("select highlight(notes_fts, 1, '>>', '<<') from notes_fts where notes_fts match 'demo'")
# -----------
# ===========
db.ex("select snippet(notes_fts, 1, '>>', '<<', '...', 6) from notes_fts where notes_fts match 'demo'")
# -----------
# # ===========
create_tags_table(db)
# # -----------
# ===========
add_tag(db, 'test', None)
# -----------
# ===========
add_tag(db, 'test', 1)
# -----------
# ===========
db.ex('select * from tags where tag = "test" and parent_id IS NULL')
# -----------
# ===========
db.ex('select * from tags')
# -----------
# # ===========
pprint(db.ex("select * from sqlite_master where type='table'"))
# # -----------
# # ===========
db_path.unlink()
# # -----------
