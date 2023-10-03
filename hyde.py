"""
Generate HTML for whole zetellkasten
"""
from pathlib import Path
import subprocess as sp

import zekell

# zekell_dir = zekell.ZK_PATH
# html_dir = zekell.ZK_PATH / 'html'
zekell_dir = Path('./dummy_proto').absolute()
html_dir = zekell_dir / 'html'
html_dir.mkdir(exist_ok=True)
index_path = html_dir / 'index.html'

note_paths = zekell_dir.glob('*.md')

index_links = []
n_notes = 0
for note in note_paths:
	print(f'Processing {note.name:<30}', end='\r', flush=True)
	note_path = note.as_posix()
	new_html_path = (html_dir / note.name).with_suffix('.html').as_posix()
	output = sp.check_output([
		'pandoc',
		note_path,
		'-o',
		new_html_path
		])
	index_links.append(f'[{note.stem}]({note.stem}.html)\n\n')
	n_notes += 1
	print(f'Processed {n_notes} notes', end='\r', flush=True)

print('Generating Index', end='\r')
temp_index = zekell_dir / '_index.md'
with open(temp_index, 'wt') as f:
	f.writelines(index_links)

print('Generating Index Page')
_ = sp.check_output([
	'pandoc',
	temp_index.as_posix(),
	'-o',
	index_path.as_posix(),
	]
	)

temp_index.unlink()

print('Done')
