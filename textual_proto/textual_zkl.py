from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import (
	Button, Footer, Header, Static,
	Input,
	Pretty, ListView, ListItem, Label, MarkdownViewer
	)

import zekell as zkl

DB = zkl.db_connection(zkl.ZK_DB_PATH)

class SearchResultItem(ListItem):
	pass

class ResultsList(ListView):
	pass



class Search(Screen):

	BINDINGS = [
		("c", "new_search", "New Search"),
		]

	def compose(self) -> ComposeResult:

		# yield Header()
		yield Footer()
		yield Input(
				placeholder='Query',
				id='search_input'
			)
		# yield Results('Results')
		yield ResultsList()

	@on(Input.Submitted)
	def show_query_results(self, event: Input.Changed):
		query = zkl.mk_super_query(event.input.value)
		results = DB.ex(query)

		# self.query_one(Results).results = results
		res_list = self.query_one(ResultsList)
		res_list.clear()
		res_list.extend(
				SearchResultItem(
					Label(rl[1]),
					name=str(rl[0]),
					)
				for rl in results
			)
		# why necessary?
		res_list.index=0
		res_list.focus()

	def action_new_search(self):
		self.query_one('#search_input').focus()


	@on(ResultsList.Selected)
	def show_note(self, event: ResultsList.Selected):

		note_id = event.item.name
		self.dismiss(result=note_id)


class Note(MarkdownViewer):
	pass


class Notes(Screen):

	def compose(self) -> ComposeResult:
		yield Note(show_table_of_contents=True)


class Zekell(App):

	SCREENS = {'search': Search(), 'notes': Notes()}
	BINDINGS = [
		("s", "show_search", "Search"),
		("n", "show_notes", "Notes")
		]

	def compose(self) -> ComposeResult:
		yield Footer()

	def on_mount(self):
		self.push_screen('notes')
		self.push_screen('search', self.update_note)

	def action_show_search(self):
		self.push_screen('search', self.update_note)

	def action_show_notes(self):
		self.push_screen('notes')

	async def update_note(self, note_id: str):
		note_view = self.query_one(Note)
		note: zkl.Path = zkl.get_note_ids_from_fuzzy_id(DB, int(note_id))

		# note_view.update(note.read_text())
		await note_view.document.load(note)



if __name__ == '__main__':
	app = Zekell()
	app.run()
