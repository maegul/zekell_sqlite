from pathlib import Path
import datetime as dt
import unittest
import sqlite3 as sql

import zekell


class TestTest(unittest.TestCase):

    def test_basic(self):
        self.assertEqual('test', 'test')


class TestCreateTables(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._db_path = Path('test.db')
        cls._db = zekell.db_connection(cls._db_path, True)
        cls._note_id = 20210904100714

    def test_create_tags_table(self):

        db = self._db
        zekell.create_tags_table(db)

        table_check = db.ex(
            "select * from sqlite_master where type='table' and name='tags'")

        self.assertEqual(len(table_check), 1)

    def test_root_tag_unique(self):
        db = self._db

        test_tag = 'first_root'
        test_parent_id = None

        zekell.add_tag(db, test_tag, parent_id=test_parent_id)

        with self.assertRaises(sql.IntegrityError):
            zekell.add_tag(db, test_tag, parent_id=test_parent_id)

    def test_tag_unique(self):
        db = self._db

        test_tag = 'test_tag'
        test_parent_id = db.ex('select * from tags')[0][0]

        zekell.add_tag(db, test_tag, test_parent_id)

        with self.assertRaises(sql.IntegrityError):
            zekell.add_tag(db, test_tag, test_parent_id)

    def test_parent_id_foreign_key(self):

        with self.assertRaises(sql.IntegrityError):
            zekell.add_tag(self._db, 'bad_parent_tag', 111)

    def test_create_notes_tag(self):

        db = self._db
        zekell.create_notes_table(db)

        table_check = db.ex(
            "select * from sqlite_master where type='table' and name='notes'")

        self.assertEqual(len(table_check), 1)

    def test_fts_insert_delete_triggers(self):

        db = self._db

        db.ex(
            '''
            insert into notes
            values(?, ?, ?, ?, ?)
            ''',
            (
                self._note_id,
                'My first note',
                '''---
                title: My first note
                tags: first, demo
                ---''',
                '''This is a demo note

                Not much more to day''',
                dt.datetime.utcnow().timestamp()

            ))

        self.assertEqual(
            len(db.ex('select * from notes_fts')),
            1
            )

        db.ex('delete from notes')

        self.assertEqual(
            len(db.ex('select * from notes_fts')),
            0
            )

    def test_create_note_links_table(self):

        db = self._db
        zekell.create_note_links_table(db)

        table_check = db.ex(
            "select * from sqlite_master where type='table' and name='note_links'")

        self.assertEqual(len(table_check), 1)

    def test_note_links_foreign_key(self):

        db = self._db

        db.ex(
            '''
            insert into notes
            values(?, ?, ?, ?, ?)
            ''',
            (
                self._note_id,
                'My first note',
                '''---
                title: My first note
                tags: first, demo
                ---''',
                '''This is a demo note

                Not much more to day''',
                dt.datetime.utcnow().timestamp()

            ))

        db.ex("""
            insert into
            note_links(parent_note_id, child_note_id)
            values(?, ?)
            """,
            (self._note_id, self._note_id)
            )

        table_check = db.ex("select * from note_links")

        self.assertEqual(len(table_check), 1)

        with self.assertRaises(sql.IntegrityError):
            db.ex("""
                insert into
                note_links(parent_note_id, child_note_id)
                values(?, ?)
                """,
                (self._note_id - 1, self._note_id)
                )

        with self.assertRaises(sql.IntegrityError):
            db.ex("""
                insert into
                note_links(parent_note_id, child_note_id)
                values(?, ?)
                """,
                (self._note_id, self._note_id - 1)
                )


    @classmethod
    def tearDownClass(cls) -> None:
        cls._db.conn.close()
        cls._db_path.unlink()


if __name__ == '__main__':
    unittest.main()
