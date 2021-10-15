from pathlib import Path
import datetime as dt
import unittest
import sqlite3 as sql

import zekell


class TestSchema(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._db_path = Path('test.db')
        cls._db = zekell.db_connection(cls._db_path, True)

    def test_run_schema(self):
        zekell.db_init(self._db)

        table_check = self._db.ex(
            'select name from sqlite_master where type="table"'
            )

        self.assertNotEqual(len(table_check), 0)


class TableBase():
    @classmethod
    def setUpClass(cls) -> None:
        cls._db_path = Path('test.db')
        cls._db = zekell.db_connection(cls._db_path, True)
        zekell.db_init(cls._db)
        cls._note_id = 20210904100714

    @classmethod
    def tearDownClass(cls) -> None:
        cls._db.conn.close()
        cls._db_path.unlink()



class TestTables(TableBase, unittest.TestCase):


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

        db.ex(
            """
            insert into
            note_links(parent_note_id, child_note_id)
            values(?, ?)
            """,
            (self._note_id, self._note_id)
            )

        table_check = db.ex("select * from note_links")

        self.assertEqual(len(table_check), 1)

        with self.assertRaises(sql.IntegrityError):
            db.ex(
                """
                insert into
                note_links(parent_note_id, child_note_id)
                values(?, ?)
                """,
                (self._note_id - 1, self._note_id)
                )

        with self.assertRaises(sql.IntegrityError):
            db.ex(
                """
                insert into
                note_links(parent_note_id, child_note_id)
                values(?, ?)
                """,
                (self._note_id, self._note_id - 1)
                )

    def test_note_tag_foreign_key(self):

        db = self._db

        file_id = 123456
        db.ex(
            '''
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
        zekell.add_tag(db, 'note_tag_test', parent_id=None)
        tag_id = (
            db.ex('''
                select id from tags where tag = "note_tag_test"
            ''')
            [0][0]
        )

        # tag_id SHOULD BE id of the tag "test"
        db.ex('insert into note_tags values (?, ?)', (file_id, tag_id))

        with self.assertRaises(sql.IntegrityError):
            # 2222 should not be an available
            db.ex('insert into note_tags values (?, ?)', (file_id, 2222))


class TestTagFullPathTriggers(TableBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # cls._db_path = Path('test.db')
        # cls._db = zekell.db_connection(cls._db_path, True)
        # zekell.db_init(cls._db)
        # cls._note_id = 20210904100714
        super().setUpClass()
        db = cls._db

        db.ex('''insert into tags(tag, parent_id) values('test', NULL )''')
        db.ex('insert into tags(tag, parent_id) values("topics", NULL)')
        db.ex('''select * from tags''')
        db.ex('insert into tags(tag, parent_id) values("code", 2)')
        db.ex('insert into tags(tag, parent_id) values("sql", 2)')
        db.ex('insert into tags(tag, parent_id) values("joins", 4)')
        db.ex('insert into tags(tag, parent_id) values("functions", 3)')

    def test_full_path_insert_trigger(self):
        db = self._db

        full_path_tags = db.ex('select * from full_tag_paths')

        self.assertNotEqual(len(full_path_tags), 0)

    def test_full_path_insert_trigger_again(self):
        db = self._db

        db.ex('insert into tags(tag, parent_id) values("triggers", 4)')

        new_tag_path = db.ex('select * from full_tag_paths where tag = "triggers"')

        self.assertNotEqual(len(new_tag_path), 0)

    def test_full_path_delete_trigger(self):
        db = self._db

        db.ex('delete from tags where tag = "joins"')
        old_tag_path = db.ex('select * from full_tag_paths where tag = "joins"')

        self.assertEqual(len(old_tag_path), 0)

    def test_full_path_update_trigger(self):
        db = self._db

        # TODO
        # really want to check that all the paths have been updated too!
        # get all ids for where tag occurs in paths, and check they all match
        # with paths with the new tag

        db.ex('update tags set tag = "new functions" where tag = "functions"')

        old_tag_path = db.ex('select * from full_tag_paths where tag = "functions"')
        new_tag_path = db.ex('select * from full_tag_paths where tag = "new functions"')

        self.assertEqual(len(old_tag_path), 0)
        self.assertNotEqual(len(new_tag_path), 0)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._db.conn.close()
        cls._db_path.unlink()





if __name__ == '__main__':
    unittest.main()
