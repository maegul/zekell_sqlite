# > Create Dummy Random Testing zekell
# ie, with notes and all

# make necessary data, create notes, and batch upload
# ===========
from sys import argv
import shutil
import zekell as zk
from pathlib import Path
import random
import string
import time
import json

args = argv[1:]
assert len(args) == 2, 'Args path and n_notes must be provided'

dummy_path = Path(args[0]).absolute()
n_notes = int(args[1])

if dummy_path.exists():
    shutil.rmtree(dummy_path)
dummy_path.mkdir(exist_ok=False)
assert dummy_path.is_dir(), 'Path must be directory'

new_id = zk.make_new_note_id()
ids = [new_id + n for n in range(n_notes)]

front_matter_template = '''---
tags: {}
---
'''.format

punctuation_replace = str.maketrans({p: '' for p in string.punctuation + string.whitespace[1:]})
# alice = path('/data/alice_in_wonderland.txt').read_text()
alice_path = (Path(__file__).parent / Path('alice_in_wonderland.txt'))  # presume in main zekell dir
alice = alice_path.read_text()  # presume in main zekell dir
lines = alice.splitlines()
words = [word for word in alice.translate(punctuation_replace).split(' ') if word and word != ' ' and len(word) > 1]

tags = [tag for tag in random.sample(words, 20) if zk.tag_path_pattern.fullmatch(tag)]

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

    new_note_path = dummy_path / Path(f'{id} {title}.md')
    note_body = front_matter + text

    new_note_path.write_text(note_body)

    return new_note_path

def time_test(test_callback):
    start = time.time()
    result = test_callback()
    end = time.time()
    return end-start, result

test_times = {}
test_counts = {}
# -----------
# ===========
# make sure in appropriate directory!
for i, new_id in enumerate(ids):
    if i % 50 == 0:
        print(f'{i} / {len(ids)}', end='\r')
    _ = mk_new_note(new_id)
# -----------
# ===========
db_path = dummy_path / Path('test.db')
db_path.unlink(missing_ok=True)
db = zk.db_connection(db_path, True)
# -----------

# >> Files table with FTS
# ===========
zk.db_init(db)
print('Initial tables:', db.ex('select name from sqlite_master where type = "table"'))
# -----------
# ===========
note_paths = list(dummy_path.glob('*.md'))

test_times['batch_add'], _ = time_test(lambda :zk.add_batch_old_note(db, note_paths))
print('****')
print(f'Intended number of notes: {n_notes}')
print(f'Number of notes in files: {len(note_paths)}')
print('number of notes in database',
    db.ex('select count(*) from notes')
    )

# > Tests

# >> add a new note

add_new_note_times = []
new_note_ids = [ids[-1] + n for n in range(1, 11)]
for i in new_note_ids:
    new_note_path = mk_new_note(i)
    add_note_time, _ = time_test(lambda: zk.add_old_note(db, new_note_path))
    add_new_note_times.append(add_note_time)

test_times['add_new_note'] = add_new_note_times


# >> Query title single words FTS search

test_title_words = random.sample(words, 10)

title_single_word_times = []
title_single_word_counts = []
for w in test_title_words:
    title_fts_time, counts = time_test(lambda: len(db.ex(zk.mk_super_query(f'title: {w}'))))
    title_single_word_times.append(title_fts_time)
    title_single_word_counts.append(counts)

test_times['title_single_word_fts']  = title_single_word_times
test_counts['title_single_word_fts'] = title_single_word_counts

# >> Query title three words FTS search


title_three_word_times = []
title_three_word_counts = []
for i in range(10):
    # test_title_words = ' OR '.join(random.sample(words, 3))
    test_title_words = ' OR '.join(
        random.sample(path.stem.split()[1:], 1)[0]
        for path in random.sample(note_paths, 3)
        )

    title_fts_time, counts = time_test(lambda: len(db.ex(zk.mk_super_query(f'title: {test_title_words}'))))
    title_three_word_times.append(title_fts_time)
    title_three_word_counts.append(counts)

test_times['title_three_word_fts'] = title_three_word_times
test_counts['title_three_word_fts'] = title_three_word_counts

# >> body FTS

body_times = []
body_counts = []

for i in range(10):
    test_body_words = ' OR '.join(random.sample(words, 3))

    body_fts_time, counts = time_test(lambda: len(db.ex(zk.mk_super_query(f'body: {test_body_words}'))))
    body_times.append(body_fts_time)
    body_counts.append(counts)

test_times['body_three_word_fts'] = body_times
test_counts['body_three_word_fts'] = body_counts


# >> body and title FTS

title_body_times = []
title_body_counts = []

for i in range(10):
    test_title_words = ' OR '.join(
        random.choice(path.stem.split()[1:])
        for path in random.sample(note_paths, 3)
        )
    test_body_words = ' OR '.join(random.sample(words, 3))

    body_fts_time, counts = time_test(lambda: len(
        db.ex(zk.mk_super_query(f'title: {test_title_words}; body: {test_body_words}'))))
    title_body_times.append(body_fts_time)
    title_body_counts.append(counts)

test_times['title_body_three_word_fts'] = title_body_times
test_counts['title_body_three_word_fts'] = title_body_counts


# >> tags

tag_times, tag_counts = [], []

for i in range(10):
    test_tags = ','.join(random.sample(tags, 3))

    tags_time, counts = time_test(lambda: len(
        db.ex(zk.mk_super_query(f'tag: {test_tags}')))
        )
    tag_times.append(tags_time)
    tag_counts.append(counts)

test_times['tags_three'] = tag_times
test_counts['tags_three'] = tag_counts


# >> tags and body

body_tag_times, body_tag_counts = [], []

for i in range(10):
    body_test_tags = ','.join(random.sample(tags, 3))
    test_body_words = ' OR '.join(random.sample(words, 3))

    body_tags_time, counts = time_test(lambda: len(
        db.ex(zk.mk_super_query(f'tag: {body_test_tags}; body: {test_body_words}')))
        )
    body_tag_times.append(body_tags_time)
    body_tag_counts.append(counts)

test_times['body_tags_three'] = body_tag_times
test_counts['body_tags_three'] = body_tag_counts


print(test_times)
print(test_counts)

# > Write results to file

times_path = Path(__file__).absolute().parent / Path(f'test_times_{n_notes}_notes.json')
counts_path = Path(__file__).absolute().parent / Path(f'test_counts_{n_notes}_notes.json')

times_path.write_text(json.dumps(test_times))
counts_path.write_text(json.dumps(test_counts))
# -----------
