# ===========
from zekell import *
import datetime as dt
# -----------

# > Testing
# ===========
db.conn.close()
# -----------
# ===========
db_path = Path('test.db')
# -----------
# ===========
db_path.unlink()
# -----------
# ===========
db = db_connection(db_path, True)
# # -----------
# >> Files table with FTS
# ===========
db_init(db)
# -----------
db.ex('select name from sqlite_master where type = "table"')
# ===========

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


# >> Note Links
# ===========
db.ex("select * from notes")
# -----------
# ===========
create_note_links_table(db)
# -----------
# ===========
db.ex('select * from notes')
db.ex('select * from note_links')
# -----------
# ===========
db.ex("""
    create table test_fk(
        id integer primary key,
        ref_id integer,
        cite_id integer,
        foreign key (ref_id) references notes (id),
        foreign key (cite_id) references notes (id)
    )
    """)
# -----------
# ===========
db.ex("""
    insert into test_fk(ref_id, cite_id) values(20210904100714, 163071404)
    """)
# -----------
# ===========
db.ex('select * from test_fk')
# -----------
# ===========
db.ex("""
    insert into
    note_links(parent_note_id, child_note_id)
    values(1630714042, 20210904100714)
    """)
# -----------
# ===========
db.ex("""
    insert into
    note_links(parent_note_id, child_note_id)
    values(163071404, 20210904100714)
    """)
# -----------
# ===========
db.ex("""
    insert into
    note_links(parent_note_id, child_note_id)
    values(1630714042, 2021090410071)
    """)
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


# > Instantiating from schema file

# ===========
db = db_connection(Path('test.db'), True)
# -----------
# ===========
schema = Path('schema.sql').read_text()
print(schema)
# -----------
# ===========
db.ex('select * from sqlite_master')
# -----------
# ===========
db.cursor.executescript(schema)
# -----------
# ===========
db.ex('select name from sqlite_master where type="table"')
# -----------
# ===========
db.ex('pragma foreign_keys')
# -----------
# ===========
import datetime as dt
        db.ex(
            '''
            insert into notes
            values(?, ?, ?, ?, ?)
            ''',
            (
                123456,
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
db.ex('select id,* from notes')
# -----------

# > note_tags_table
# ===========
db = db_connection(Path('test.db'), True)
# -----------
# ===========
db.ex('select name from sqlite_master')
# -----------
# ===========
db.ex('drop table note_tags')
# -----------
# ===========
query = '''
create table if not exists
    note_tags (
        note_id integer,
        tag_id integer,
        foreign key (note_id) references notes (id),
        foreign key (tag_id) references tags (id)
        );
'''
# -----------
# ===========
db.ex(query)
# -----------
# ===========
db.ex('''
    insert into note_tags values (1, 1)
    ''')
# -----------
# ===========
db_init(db)
# -----------
# ===========
db.ex('select name from sqlite_master')
# -----------
# ===========
file_id = int(dt.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
db.ex('''
    insert into notes
    values(?, ?, ?, ?, ?)
    ''',
    (
        file_id,
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
file_id
# -----------
# ===========
db.ex('select * from notes')
# -----------
# ===========
add_tag(db, 'test')
# -----------
# ===========
db.ex('select * from tags')
# -----------
# ===========
db.ex('insert into note_tags values (?, ?)', (file_id, 1))
# -----------
# ===========
db.ex('select * from note_tags')
# -----------
# ===========
# shouldn't work because of foreign key constraint
db.ex('insert into note_tags values (?, ?)', (file_id, 2))
# -----------
# ===========
db.ex('select id from tags')[0][0]
# -----------


# > Tags and auto parent tables

# ===========
db.ex('drop table if exists tags')
db.ex('drop table if exists full_tag_paths')
# -----------
# ===========
db.ex('''
    insert into tags(tag, parent_id) values(
        'test',
        NULL
    )
    ''')
# -----------
# ===========
db.ex('insert into tags(tag, parent_id) values("topics", NULL)')
# -----------
# ===========
db.ex('''select * from tags''')
# -----------
# ===========
db.ex('insert into tags(tag, parent_id) values("code", 2)')
db.ex('insert into tags(tag, parent_id) values("sql", 2)')
db.ex('insert into tags(tag, parent_id) values("joins", 4)')
db.ex('insert into tags(tag, parent_id) values("functions", 3)')
# -----------
# ===========
db.ex('insert into tags(tag, parent_id) values("code", 22)')
# -----------
# ===========
db.ex('''
    select id from tags where tag == 'topics'
    ''')
# -----------
# ===========
db.ex('''
    select m.id, p.tag parent, m.tag, p.id parentid
    from tags m
    left join tags p
    on m.parent_id = p.id
    ''')
# -----------
# ===========
db.ex('''
    with recursive tags_parents(id, tag, parent_id, parent) as
        (
        select a.id, a.tag, a.parent_id, b.tag as parent
        from tags a
        left join tags b
        on a.parent_id = b.id
        ),
    pnts(id, tag, parent_id, id_path, tag_path) as
        (
        select
            id, tag, parent_id,
            ifnull(parent_id, '-') as id_path, ifnull(parent, '-') as tag_path
        from tags_parents
        where parent_id is NULL
        union
        select
            m.id, m.tag, m.parent_id,
            ifnull(pnts.id_path, '-') || '/' || pnts.id as id_path,
            ifnull(pnts.tag_path, '-') || '/' || pnts.tag as tag_path
        from tags_parents m
        join pnts
        on pnts.id = m.parent_id
        order by m.parent_id desc
        )
    select
        id, tag,
        id_path || '/' || id as full_path,
        tag_path || '/' || tag as full_tag_path
    from pnts
    ''')

# -----------
# ===========
db.ex('''
    create table full_tag_paths as
    with recursive tags_parents(id, tag, parent_id, parent) as
        (
        select a.id, a.tag, a.parent_id, b.tag as parent
        from tags a
        left join tags b
        on a.parent_id = b.id
        ),
    pnts(id, tag, parent_id, id_path, tag_path) as
        (
        select
            id, tag, parent_id,
            ifnull(parent_id, '-') as id_path, ifnull(parent, '-') as tag_path
        from tags_parents
        where parent_id is NULL
        union
        select
            m.id, m.tag, m.parent_id,
            ifnull(pnts.id_path, '-') || '/' || pnts.id as id_path,
            ifnull(pnts.tag_path, '-') || '/' || pnts.tag as tag_path
        from tags_parents m
        join pnts
        on pnts.id = m.parent_id
        order by m.parent_id desc
        )
    select
        id, tag,
        id_path || '/' || id as full_path,
        tag_path || '/' || tag as full_tag_path
    from pnts
    ''')

# -----------
# ===========
db.ex('select * from full_tag_paths')
# -----------








