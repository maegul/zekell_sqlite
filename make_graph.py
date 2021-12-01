#! /usr/bin/env python3

import zekell as zk
import subprocess as sp

db = zk.db_connection(zk.ZK_DB_PATH)

q = '''
	select a.parent_note_id, b.title, a.child_note_id, c.title
	from note_links a
	left join notes b on a.parent_note_id = b.id
	left join notes c on a.child_note_id = c.id
'''

links = db.ex(q)

all_nodes = set()
for l in links:
    all_nodes.add((l[0], l[1]))
    all_nodes.add((l[2], l[3]))

lines = []
lines.append('digraph test {\n')
lines.append('rankdir=LR;\n')
for n in all_nodes:
    lines.append(f'\t{n[0]} [label="{n[1]}"]\n')
lines.append('\n')
for l in links:
    lines.append(f'\t{l[0]} ->{l[2]}\n')
lines.append('}')

graph_file = zk.ZK_PATH / zk.Path('zk_graph.dot')
out_file = graph_file.with_suffix('.svg')

with open(graph_file, 'w') as f:
	f.writelines(lines)

_ = sp.check_output(
		['dot', '-Tsvg', graph_file.as_posix(), '-o', out_file.as_posix()]
	)

_ = sp.check_output(['open', '-a', 'Safari', out_file.as_posix()])
