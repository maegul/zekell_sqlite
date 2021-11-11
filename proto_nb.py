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

# >> Testing Batch ex
# ===========
db.ex([
    '''insert into tags(tag, parent_id) values('test', NULL )''',
    'insert into tags(tag, parent_id) values("topics", NULL)',
    ])
# -----------
# ===========
db.ex([
    'insert into tags(tag, parent_id) values("code", 2)',
    'insert into tags(tag, parent_id) values("sql", 2)',
    'insert into tags(tag, parent_id) values("joins", 4)',
    'insert into tags(tag, parent_id) values("functions", 3)'
    ])
# -----------
# ===========
db.ex('insert into tags(tag, parent_id) values("rollbacktest", 2)')
# -----------
# ===========
db.ex([
    'insert into tags(tag, parent_id) values("rollbacktest2", 2)',
    'insert into tags(tag, parent_id) values("anothertest", 4)',
    'insert into tags(tag, parent_id) values("functions", 3)'
    ])
# -----------
# ===========
db.ex('select * from tags')
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
new_note_path = Path('prototype/20211022003326 first_note.md')
# -----------
# ===========
update_note(db, new_note_path)
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
note_path = Path('prototype/20211022010525 first.md')
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

    return new_id

# -----------
db.ex('select * from tags')
db.ex('select * from full_tag_paths')
# ===========
add_new_tag_path(db, 'test/path/new')
# -----------
# ===========
add_new_tag_path(db, 'convenience/notes/tags/paths/new')
# -----------
# ===========
add_new_tag_path(db, 'notes/tags/paths/new')
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


# > Sorting mod times
# ===========
import datetime as dt
# -----------
# ===========
now_ts = dt.datetime.utcnow().timestamp()
# -----------
# ===========
db.ex('drop table dt_test')
# -----------
# ===========
db.ex('create table dt_test(dti integer, dtn real, dtt text)')
# -----------
# ===========
n = range(1000)
qs = ['insert into dt_test(dti, dtn, dtt) values(?,?,?)' for _ in n]
params = [(int(now_ts + i), float(now_ts + i), str(now_ts + i)) for i in n]

db.ex(qs, params)
# -----------
# ===========
o = db.ex('select * from dt_test')
# -----------
o[0]
# ===========
%timeit o = db.ex('select * from dt_test order by dti desc')
# -----------
# ===========
%timeit o = db.ex('select * from dt_test order by dtn desc')
# -----------
# ===========
%timeit o = db.ex('select * from dt_test order by dtt desc')
# -----------
dt.datetime.utco[0]


# > Create Dummy Random Testing zekell
# ie, with notes and all

# make necessary data, create notes, and batch upload
# ===========
import random
import string

n_notes = 300
new_id = make_new_note_id()
ids = [new_id + n for n in range(n_notes)]

front_matter_template = '''---
tags: {}
---
'''.format

punctuation_replace = str.maketrans({p: '' for p in string.punctuation + string.whitespace[1:]})

# alice = Path('/Data/alice_in_wonderland.txt').read_text()
alice = Path('./alice_in_wonderland.txt').read_text()  # presume in main zekell dir
lines = alice.splitlines()
words = [word for word in alice.translate(punctuation_replace).split(' ') if word and word != ' ']

tags = random.sample(words, 15)

mk_tags = lambda: ','.join(random.sample(tags, random.choice(range(1, 4))))
mk_front_matter = lambda: front_matter_template(mk_tags())
mk_text = lambda: '\n'.join(random.sample(lines, 20))
mk_link = lambda: f'[{"".join(random.sample(string.ascii_lowercase, 7))}](/{random.choice(ids)})'
mk_title = lambda: (' '.join(random.sample(words, random.randint(1, 5))))

def mk_note_text():
    text = mk_text()
    n_chars = len(text)-1
    n_links = random.randint(0, 10)
    link_locations = [0] + sorted(random.sample(range(n_chars), n_links)) + [len(text)]
    link_location_slices = list(zip(link_locations, link_locations[1:]))
    new_text = ''.join(
        text[a:b] + mk_link()
        for a, b in link_location_slices)

    return new_text

def mk_new_note(id):

    title = mk_title()
    front_matter = mk_front_matter()
    text = mk_note_text()

    new_note_path = Path(f'{id} {title}.md')
    note_body = front_matter + text

    new_note_path.write_text(note_body)

# -----------
# ===========
cd dummy_proto
# -----------
# ===========
# make sure in appropriate directory!
for new_id in ids:
    if new_id % 50 == 0:
        print(new_id)
    mk_new_note(new_id)
# -----------
# ===========
db_path = Path('test.db')
# -----------
# ===========
db_path.unlink()
# -----------
# ===========
db = db_connection(db_path, True)
# -----------

# >> Files table with FTS
# ===========
db_init(db)
# -----------
# ===========
db.ex('select name from sqlite_master where type = "table"')
# -----------
# ===========
note_paths = list(Path('.').glob('*.md'))
# -----------
# ===========
add_batch_old_note(db, note_paths)
db.ex('select * from notes limit 2')
db.ex('select * from note_links limit 2')
db.ex('select * from full_tag_paths')
# -----------

# >> Query Prototyping

# >>> Get database
# ===========
cd dummy_proto
db = db_connection(Path('test.db'))
# -----------
# ===========
db.ex('select count(*) from notes')
# -----------

# >>> All notes with particular tag
# ===========
db.ex('select * from full_tag_paths')
# -----------
# ===========
db.ex('select * from note_tags limit 15')
# -----------
# ===========
# all note_ids with tag id
tag_id = 8
o = db.ex('select note_id from note_tags where tag_id = ?', [tag_id])
len(o)
o[:10]
# -----------
# ===========
# note ids and titles
o = db.ex('''
    select note_id, notes.title from note_tags
    left join notes
    on notes.id = note_tags.note_id
    where tag_id = ?
    ''',
    [8])
o[:10]
# -----------

# >>> All notes that are direct children of particular note
# ===========
o = db.ex('select * from note_links')
o[:10]
# -----------
# ===========
# random note id
note_id = db.ex(
    'select id from notes where id in (select id from notes order by random() limit 1)'
    )[0][0]
note_id
# -----------
# ===========
o = db.ex('select child_note_id from note_links where parent_note_id = ?', [note_id])
o[:10]
# -----------

# >>> All children of a set of parents
# ===========
note_ids = [n[0] for n in o]
# sooo ... this isn't a thing ... can't just pass a list
# or anything other than a basic type (eg int or string)
o = db.ex('select child_note_id from note_links where parent_note_id in ?',[note_ids])
# -----------
# iter args
# ===========
mk_iter_arg = lambda args: f"({','.join('?' for _ in args)})"
o = db.ex(
    f'select child_note_id from note_links where parent_note_id in {mk_iter_arg(note_ids)}',
    note_ids)
len(o)
# -----------
mk_iter_arg(['hello', 'world'])

# This really gets into recursive queries
# One may wish to get all children notes that are n levels deep in the query


# >>> All parents of a note

# ===========
# random note id
note_id = db.ex(
    'select id from notes where id in (select id from notes order by random() limit 1)'
    )[0][0]
note_id
# -----------
# ===========
o = db.ex('select parent_note-id from note_links where child_note_id = ?', [note_id])
o[:10], len(o)
# -----------

# again, recursion may make sense here at some point



# >>> Full Text Search

# ===========
# match against title col
o = db.ex('select rowid, title from notes_fts where title match "alice"')
o[:10], len(o)
# -----------
# ===========
# match any col (?)
o = db.ex('select rowid, title from notes_fts where notes_fts match "alice"')
o[:10], len(o)
# -----------
# ===========
o = db.ex('select rowid, title from notes_fts where notes_fts match "hookah"')
o[:10], len(o)
# -----------
# ===========
o = db.ex('select rowid, title from notes_fts where notes_fts match "hookah alice"')
o[:10], len(o)
# -----------
# ===========
o = db.ex('''
    select rowid, title, snippet(notes_fts, -1, "**>", "<**", "...", 10)
    from notes_fts where title match "hookah"
    ''')
o[:10], len(o)
# -----------
# ===========
# two word phrase with wild card
o = db.ex('''
    select rowid, snippet(notes_fts, -1, "**>", "<**", "...", 10)
    from notes_fts where title match "hookah + and*"
    ''')
o[:10], len(o)
# -----------


# >>> Compete (super) query
# ===========
db.ex('select * from full_tag_paths')
# -----------
# ===========
db.ex('select id from full_tag_paths where full_tag_path = "terms"')
# -----------
# ===========
db.ex('select note_id from note_tags where tag_id = 12')
# -----------
# ===========

# -----------
# Maybe CTEs are the answer!?
# One CTE for each potential component of the super query ... ?
# join for AND, and Union for OR (in terms of combining multiple queries)
# ===========
q = '''
with tagged_notes(note_id) as (
    select note_id from note_tags as p
    where tag_id = (
        select id from full_tag_paths where full_tag_path = "terms"
        )
    )
select distinct parent_note_id from note_links
left join tagged_notes
on tagged_notes.note_id = note_links.child_note_id
'''
db.ex(q)
# -----------
# ===========
# all children of all notes tagged "terms"
q = '''
with
tagged_notes(note_id) as (
    select note_id from note_tags as p
    where tag_id = (
        select id from full_tag_paths where full_tag_path = "terms"
        )
    ),
parent_notes(note_id, child_note_id) as (
    select parent_note_id, child_note_id from note_links
)
select distinct parent_notes.note_id
from tagged_notes left join parent_notes
    on tagged_notes.note_id = parent_notes.note_id
'''
db.ex(q)
# -----------
# ===========
db.ex('select * from note_links where parent_note_id = 20211031083275')
# -----------
# ===========
# >>>> tag_cte
# can get more complex with and/or with multiple tags
tag_cte = '''
tagged_notes(note_id) as (
    select note_id from note_tags
    where tag_id = (
        select id from full_tag_paths where full_tag_path = "{}"
    )
)
'''.format
# -----------
# ===========
# >>>> child_cte
child_cte = '''
child_notes(note_id) as (
    select child_note_id from note_links
    where parent_note_id = "{}"
)
'''.format
# -----------
# >>>> FTS Play
# ===========
db.ex('select rowid,title from notes_fts where title match "alice"')
# boolean operators are case sensitive
db.ex('select title from notes_fts where title match "hookah OR alice"')
# implict AND
db.ex('select title from notes_fts where title match "guests alice"')
# wild card
db.ex('select title from notes_fts where title match "gue* alice"')
# parens
db.ex('select title from notes_fts where notes_fts match "title : alice AND (old OR gues*)"')
# highligh aux function
db.ex('select highlight(notes_fts, 0, \'>>\', \'<<\') from notes_fts where title match "alice AND (old OR gues*)"')
# -----------
# ===========
# near function and phrases
# implicit AND on multiple terms! (kinda like fuzzy find)
db.ex('select title, bm25(notes_fts) from notes_fts where title match "alice a"')
# a single phrase
db.ex('select title from notes_fts where title match "alice + a"')
# near function and distance
db.ex('select title from notes_fts where title match "NEAR(alice a, 2)"')
# only adjacents found
db.ex('select title from notes_fts where title match "NEAR(alice a, 1)"')
# -----------
# ===========
# bm25 ... not the same as fuzzy find though
db.ex('''
    select highlight(notes_fts, 0, \'>>\', \'<<\'),
    highlight(notes_fts, 1, \'>>\', \'<<\'),
    bm25(notes_fts)
    from notes_fts
    where notes_fts match "alice sister"
    order by bm25(notes_fts)
    ''')
# -----------
# ===========
# >>>> title_cte
title_cte = '''
title_notes(note_id) as (
    select rowid from notes_fts
    where title match "{}"
)
'''.format
# -----------
# ===========
# testing title_cte
db.ex(f'''with {title_cte('alice')} select * from title_notes''')
db.ex(f'''with {title_cte('alice a')} select * from title_notes''')
db.ex(f'''with {title_cte('alice in*')} select * from title_notes''')
db.ex(f'''with {title_cte('alice AND (in* OR beg*)')} select * from title_notes''')
# -----------
# ===========
q = f'''
    with {tag_cte('terms')}
    select * from tagged_notes
    '''
db.ex(q)
# -----------
# ===========
db.ex(f'''
    with {child_cte(20211031083010)}
    select * from child_notes
    ''')
# -----------
# ===========
# tags of children of parent
db.ex(f'''
    with {child_cte(20211031083010)}
    select tags.tag
    from child_notes
    left join note_tags on note_tags.note_id = child_notes.note_id
    left join tags on note_tags.tag_id = tags.id
    '''
    )

# -----------
# ===========
# all notes children of 20211031083010 AND tagged "she"
db.ex(f'''
    with
    {child_cte(20211031083010)},
    {tag_cte('she')}
    select a.note_id
    from child_notes a
    inner join tagged_notes b
        on a.note_id = b.note_id
    ''')
# -----------
# ===========
db.ex('''
    select notes.title from note_tags
    inner join notes on note_tags.note_id = notes.id
    where tag_id = 10
    limit 50
    ''')

# -----------
# ===========
# notes with alice in title and tag she
# could be faster with note_tags indexed??
db.ex(f'''
    with
    {title_cte('alice')},
    {tag_cte('she')}
    select z.id, z.title
    from title_notes a
    inner join tagged_notes b
        on a.note_id = b.note_id
    inner join notes z
        on b.note_id = z.id
    ''')
# -----------
# ===========
# children of notes with alice in title
# not quite simple here ... how generalise simple joins like this ...?
# the "children of" part really is just "children of" ... so maybe pretty simple in the end
# and similarly for "parents of"
db.ex(f'''
    with
    {title_cte('alice')}
    select b.child_note_id
    from title_notes a
    inner join note_links b
        on a.note_id = b.parent_note_id
    ''')
# -----------
# ===========
# CHILDREN OF notes with alice in title and tag she
# adaptation of above
# how handle ad hoc column names for note_links and join on notes z (child_note_id)?
    # I guess just handle the ad hoc nature of prefixing with "parent_/child_"
db.ex(f'''
    with
    {title_cte('alice')},
    {tag_cte('she')}
    select z.title, z.id
    from title_notes a
    inner join tagged_notes b
        on a.note_id = b.note_id
    inner join note_links x
        on b.note_id = x.parent_note_id
    inner join notes z
        on x.child_note_id = z.id
    ''')
# -----------
db.cursor.description

# >>>> Complex Tag queries play
# ===========
db.ex('select * from note_tags limit 20')
# -----------
# ===========
db.ex('select note_id, count(tag_id) from note_tags group by note_id')
# -----------
db.ex('select * from tags')
# ===========
# AND
# count = 2 must match number of tags using
# must get ids as well
db.ex('''
    select note_id, count(*)
    from note_tags
    where tag_id in (7, 11)
    group by note_id
    having count(note_id) = 2
    ''')
# -----------
# ===========
# subquery for getting id by tag_path
db.ex('''
    select note_id, count(*)
    from note_tags
    where tag_id in (
        select id from full_tag_paths where full_tag_path in ("offer", "might")
    )
    group by note_id
    having count(note_id) = 2
    ''')
# -----------
# ===========
# XOR
# count = 1 means only one
db.ex('''
    select note_id, count(*)
    from note_tags
    where tag_id in (7, 11)
    group by note_id
    having count(note_id) = 1
    ''')
# -----------
# ===========
# OR
# no count means any number match
db.ex('''
    select note_id, count(*)
    from note_tags
    where tag_id in (7, 11)
    group by note_id
    ''')
# -----------
# >>>> And tag cte
ts = "offer might"
tuple(ts.split(' '))
ts = "offer, might"
tuple(t.strip() for t in ts.split(','))
# ===========
def tag_and_cte(tags: str):
    tags_tuple = tuple(tags.split(' '))
    cte = f'''
    tagged_notes(note_id) as (
        select note_id
        from note_tags
        where tag_id in (
            select id from full_tag_paths where full_tag_path in {tags_tuple}
        )
        group by note_id
        having count(note_id) = {len(tags_tuple)}
    )
    '''
    return cte
# -----------
# >>>> Or tag cte
# ===========
def tag_or_cte(tags: str):
    tags_tuple = tuple(t.strip() for t in tags.split(','))
    cte = f'''
    tagged_notes(note_id) as (
        select note_id
        from note_tags
        where tag_id in (
            select id from full_tag_paths where full_tag_path in {tags_tuple}
        )
        group by note_id
    )
    '''
    return cte
# -----------
# ===========
db.ex(f'''
    with
    {tag_and_cte('offer might')}
    select * from tagged_notes
    ''')
# -----------
# ===========
db.ex(f'''
    with
    {tag_or_cte('offer, might')}
    select * from tagged_notes
    ''')
# -----------

# >>>> query DSL

# CTE componets
# ===========
from textwrap import dedent

tag_cte = '''
tagged_notes(note_id) as (
    select note_id from note_tags
    where tag_id = (
        select id from full_tag_paths where full_tag_path = "{}"
    )
)
'''.format

title_cte = '''
title_notes(note_id) as (
    select rowid from notes_fts
    where title match "{}"
)
'''.format

body_cte = '''
body_notes(note_id) as (
    select rowid from notes_fts
    where body match "{}"
)
'''.format

child_cte = '''
child_notes(note_id) as (
    select child_note_id from note_links
    where parent_note_id = "{}"
)
'''.format

def tag_or_cte(tags: str):
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

# def tag_wrapper(tags: str):

# -----------
# ===========
cte_map = {
    'title': title_cte,
    'body': body_cte,
    'child': child_cte,
    'tag': tag_cte,
    'tag_or': tag_or_cte,
    'tag_and': tag_and_cte
}

cte_table_name_map = {
    'title': 'title_notes',
    'body': 'body_notes',
    'child': 'child_notes',
    'tag': 'tagged_notes',
    'tag_or': 'tagged_or_notes',
    'tag_and': 'tagged_and_notes'
}

def query_tag_redirect(parsed_q: dict):

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
# -----------
# ===========
import string
cte_aliases = list(string.ascii_lowercase)

def mk_super_query(q: str, notes_cols = None):

    parsed_q = dict([
        [ssq.strip() for ssq in sq.strip().split(':')]
        for sq in q.split(';')
    ])
    parsed_q = query_tag_redirect(parsed_q)

    sq = 'with' + ','.join(cte_map[k](v) for k,v in parsed_q.items())
    if not notes_cols:
        notes_cols = ['id']
    selection_cols = f"select {','.join(f'z.{col}' for col in notes_cols)}\n"
    sq += selection_cols

    for i, k in enumerate(parsed_q.keys()):
        alias = cte_aliases[i]
        prev_alias = cte_aliases[i-1]
        if i == 0:
            sq += f"from {cte_table_name_map[k]} {alias}\n"
        else:
            sq += f"inner join {cte_table_name_map[k]} {alias} on {prev_alias}.note_id = {alias}.note_id\n"
    sq += f"inner join notes z on {alias}.note_id = z.id"

    return sq
# -----------
# ===========
db.ex(mk_super_query('body: alice; tag: she; title: about', ['id', 'title']))
# -----------

# implicit and in above ... how or (using outer join?)
# not the highest priority

# > Fuzzy note id

# ===========
db.ex('select id from notes limit 10')
# -----------
# ===========
db.ex('select id from notes where id like ("%" || ?)', [83015])
# -----------
# ===========
def get_note_ids_from_fuzzy_id(db: DB, fuzzy_id: int):

    note_ids = db.ex('select id, title from notes where id like ("%" || ?)', [fuzzy_id])
    return note_ids
# -----------
# ===========
note_cands = get_note_ids_from_fuzzy_id(db, 83015)
if len(note_cands) > 1:
    display_rows(db, note_cands)
else:
    note_path = make_note_file_name(NoteName(*note_cands[0]))
# -----------
