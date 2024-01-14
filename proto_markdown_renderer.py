import re
from typing import Callable

# +
text = '''
bucket-name: `s3://errol-backup-bucket`

Designated user: `maegul_backup`

* Does **not** have a *console log* in password at the moment
* What kind of `raw *content*` will this be?
* Set up with credentials with aws cli on macbookpro (2013)
* See [link to manual](http://whatever.com)

## Configuration

* Indefinite versioning
* Infrequent access
* user `maegul_backup` is intended for use with a custom and general s3 set of permissions
* A budget is set with alerts at reaching (or being forecast to reach) $1 per month (!!)

## Automation and Scripting

See `phd_backup_s3.py` in `~/bin`
'''

text_lines = text.splitlines()
# -

# +
class MDElement:
	def __init__(
			self,
			pattern: re.Pattern, renderer: Callable[[str, re.Match], str],
			end: bool = False,
			exclusive: bool = False
			):
		self.pattern = pattern
		self.renderer = renderer
		self.end = end
		self.exclusive = exclusive
# -
# +
heading_pattern = re.compile(r'^(#+) (.+)$')
def heading_render(line: str, match: re.Match) -> str:
	new_line = f'<h{len(match.group(1))}>{match.group(2)}</h{len(match.group(1))}>'
	return new_line

heading = MDElement(heading_pattern, heading_render, end=True)
# -
# +
raw_pattern = re.compile(r'\`(.+?)\`')
def raw_renderer(line: str, match: re.Match):
	new_line = ''.join((
		line[:match.span(0)[0]],
		f'<code>{match.group(1)}</code>',
		line[match.span(0)[1]:]
		))
	return new_line

raw = MDElement(raw_pattern, raw_renderer)
# -
# +
emph_pattern = re.compile(r'(\*{1,3})(\S.+?\S)(\*{1,3})')
def emph_renderer(line: str, match: re.Match):
	beg, end = match.group(1), match.group(3)

	# non-matching tags
	if len(beg) != len(end):
		# print('not matching tags')
		return line

	tags = [
		'em',
		'b',
		'strong'
	]
	new_tag = tags[len(beg)]

	new_line = ''.join((
		line[:match.span(0)[0]],
		f'<{new_tag}>{match.group(2)}</{new_tag}>',
		line[match.span(0)[1]:]
		))

	return new_line

emph = MDElement(emph_pattern, emph_renderer)
# -

# HOW make raw exclusive!!
# Have to get to proper parsing / state machine?
# But, how tokenize? Go character by character?

# +
md_elements = (
	heading,
	raw,
	emph
	)
# -

# +
t = m.span()
a = (8, 11)
b = (15, 20)
c = (7, 9)
# -
# +
s = c
t[0]-s[0], t[1]-s[1], s[1]-s[0], t[1]-t[0]
# -
# tests = (
# 		s[0] > t[0],
# 		s[1] > t[1],
# 		s[1] > t[0],
# 		s[0] > t[1],
# 	)
# tests[]



# +
for line in text_lines:
	new_line = line
	# for element in md_elements:
	element_idx = 0
	element = md_elements[element_idx]
	for _ in range(1000):  # timeout after 1000 matches??!!
		# print(line, element.pattern)
		match = element.pattern.search(new_line)
		if match:
			new_line = element.renderer(new_line, match)
			print('')
			print(line)
			print(new_line)
			if element.end:  # done with the line
				break
		else:
			if (element_idx + 1) >= len(md_elements):  # no more elements
				break
			element_idx += 1
			element = md_elements[element_idx]
# -
































