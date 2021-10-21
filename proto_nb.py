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
# ===========
db.ex('select name from sqlite_master where type = "table"')
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

# >> reset tags
# ===========
db.ex('drop table if exists tags')
db.ex('drop table if exists full_tag_paths')
# -----------
# ===========
db.ex('select * from tags')
# -----------

# >> add tags
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
# should fail with foreign key constraint
db.ex('insert into tags(tag, parent_id) values("code", 22)')
# -----------
# ===========
db.ex('''
    select id from tags where tag == 'topics'
    ''')
# -----------

# >> join parents
# ===========
db.ex('''
    select m.id, p.tag parent, m.tag, p.id parentid
    from tags m
    left join tags p
    on m.parent_id = p.id
    ''')
# -----------

# >> full tag paths proto
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
            ifnull(parent_id, '-') as id_path,
            ifnull(parent, '-') as tag_path
        from tags_parents
        where parent_id is NULL
        union
        select
            m.id, m.tag, m.parent_id,
            pnts.id_path || '/' || pnts.id as id_path,
            pnts.tag_path || '/' || pnts.tag as tag_path
        from tags_parents m
        join pnts
        on pnts.id = m.parent_id
        order by m.parent_id desc
        )
    select
        id, tag,
        ltrim(id_path || '/' || id, '-/') as full_path,
        ltrim(tag_path || '/' || tag, '-/') as full_tag_path
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

# >> Test full tag paths
# ===========
db.ex('select * from full_tag_paths')
# -----------
db.cursor.description
# ===========
db.ex('''
    update full_tag_paths
        set id = id_ud, tag = tag_ud, full_path = full_path_ud, full_tag_path = full_tag_path_ud
        from (
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
                id as id_ud, tag as tag_ud,
                id_path || '/' || id as full_path_ud,
                tag_path || '/' || tag as full_tag_path_ud
            from pnts
            )
        where id = id_ud
    ''')
# -----------
# ===========
db.ex('select * from full_tag_paths')
# -----------
# ===========
db.ex('delete from full_tag_paths')
# -----------
# ===========
db.ex('select * from full_tag_paths')
# -----------
# ===========
db.ex('insert into tags(tag, parent_id) values("trigger", 4)')
# -----------
# ===========
db.ex('select * from tags')
# -----------
# ===========
db.ex('''
    insert into full_tag_paths
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
                id as id_ud, tag as tag_ud,
                id_path || '/' || id as full_path_ud,
                tag_path || '/' || tag as full_tag_path_ud
            from pnts
    ''')
# -----------

# >> Testing full_tag_path triggers
# ===========
db.ex('select * from tags')
# -----------
# ===========
db.ex('select * from full_tag_paths')
# -----------

# test insert trigger
# ===========
db.ex('insert into tags(tag, parent_id) values("triggers", 4)')
# -----------
# ===========
db.ex('select * from tags')
db.ex('select * from full_tag_paths')
# -----------

# test delete trigger
# ===========
# error from foreign key constraint ... ?
db.ex('delete from tags where id = 2')
# -----------
# ===========
db.ex('delete from tags where tag = "triggers"')
# -----------
# ===========
db.ex('select * from tags')
db.ex('select * from full_tag_paths')
# -----------

# test update trigger
# ===========
db.ex('update tags set tag = "new functions" where tag = "functions"')
db.ex('update tags set tag = "new topics" where tag = "topics"')
# -----------
# ===========
db.ex('select * from tags')
db.ex('select * from full_tag_paths')
# -----------


# > Parsing notes
# ===========
import re
# -----------
# ===========
proto_note = (
    Path('./prototype/20200904105632 Python.mdzk')
    .read_text()
    )
# -----------
# ===========
print(proto_note)
# -----------
# ===========
front_matter_pattern = re.compile(r'(?s)^---\n(.+)\n---')
# -----------
# ===========
# -----------
# ===========
front_matter = front_matter_pattern.match(proto_note)
front_matter_data = front_matter.group(1)
meta_data = {}
for line in front_matter_data.splitlines():
    key, value = [token.strip() for token in line.split(':')]

    if key == 'tags':
        meta_data[key] = [token.strip() for token in value.split(',')]
    else:
        meta_data[key] = value

meta_data
# -----------
# ===========
link_pattern = re.compile(r'\[(.*)\]\(\/(\d{12,14})\)')
# -----------
# ===========
links = link_pattern.findall(proto_note)
links
# -----------
# ===========
link_ids = set(link[1] for link in links)
link_ids
# -----------
# ===========
note_path = Path('prototype/20200904105632 Python.mdzk')
note = parse_note(note_path)
# -----------
# ===========
note._asdict()
# -----------
# ===========
db.ex('pragma table_info(notes)')
# -----------
# ===========
db.ex('''
    insert into notes(id, title, frontmatter, body, mod_time)
    values(?, ?, ?, ?, ?)''',
    params=[note.id, note.title, note.frontmatter, note.body, dt.datetime.utcnow().timestamp()]
    )
# -----------
# ===========
db.ex('select * from notes')
# -----------

# > Adding Notes
# ===========
db.ex('select * from notes')
# -----------
# ===========
make_new_note(db, 'first_note')
# -----------
# ===========
db.ex('select * from notes')
# -----------
# ===========
ls ./prototype
# -----------
# ===========
make_new_note(db, '')
# -----------
# ===========
ls ./prototype
# -----------
# ===========
update_note(db, Path('prototype/20211019103824 first_note.md'))
# -----------
# ===========
db.ex('select * from notes')
# -----------
# ===========
delete_note(db, Path('prototype/20211019103824 first_note.md'))
# -----------


# >> Adding LInks

# Unique links?
# ===========
make_new_note(db, 'first')
# -----------
# ===========
make_new_note(db, 'second')
make_new_note(db, 'third')
make_new_note(db, 'fourth')
# -----------
# ===========
db.ex('select * from notes')
# -----------
# ===========
db.ex('select * from note_links')
# -----------
# ===========
db.ex(
    'insert into note_links(parent_note_id, child_note_id) values(?, ?)',
    [20211020035331, 20211020035334])
db.ex(
    'insert into note_links(parent_note_id, child_note_id) values(?, ?)',
    [20211020035331, 20211020035334])
# -----------
# ===========
# duplicates!?
db.ex('select * from note_links')
# -----------
# ===========
# ignore uniqueness constraing error and skip
db.ex(
    'insert or ignore into note_links(parent_note_id, child_note_id) values(?, ?)',
    [20211020035331, 20211020035334])
# -----------
# ===========
# BUT ... doesn't ignore foreign key constraints
db.ex(
    'insert or ignore into note_links(parent_note_id, child_note_id) values(?, ?)',
    [20211020035331, 123123123123])
# -----------

# >> Update note with links
# ===========
db.ex('select * from note_links')
# -----------
# ===========
note_path = Path('prototype/20211020035335 fourth.md')
update_note(db, note_path)
# -----------
# ===========
db.ex('select * from notes')
# -----------
# ===========
db.ex('select * from note_links')
# -----------
# ===========
parse_note_body(note_path.read_text())
# -----------
note_path.read_text()
# ===========
link_pattern.findall(note_path.read_text())
# -----------

# >> Adding Tags
# ===========
# get list of paths
paths = [
t[0] for t in
db.ex('select full_tag_path from full_tag_paths')
]
paths
# -----------
# ===========
paths = ['test',
 'topics',
 'topics/code',
 'topics/code/functions',
 'topics/sql',
 'topics/sql/joins']
# -----------
# ===========
new_path = 'topics/sql/recursive/theory'
# -----------
# ===========
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
# -----------

# ===========
def add_new_tag_path(db: DB, new_tag_path: str):

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

    return new_id

# -----------
db.ex('select * from tags')
db.ex('select * from full_tag_paths')
# ===========
add_new_tag_path(db, 'test/path/new')
# -----------
# ===========
add_new_tag_path(db, 'convenience/notes/tags/paths')
# -----------
# ===========
new_path_parent = max([
    tag_path for tag_path in paths
    if tag_path in new_path
])
new_path_parent
# -----------
# ===========
assert new_path.find(new_path_parent) == 0, 'not full path'
# -----------
# ===========
new_path_parent_id = db.ex(
    'select id from full_tag_paths where full_tag_path = ?',
    [new_path_parent])[0][0]
# -----------
# ===========
# plus one to omit the slash
new_tags = new_path[len(new_path_parent)+1:].split('/')
new_tags
# -----------




