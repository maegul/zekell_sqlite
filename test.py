from pathlib import Path
import unittest
import sqlite3 as sql
from unittest.main import TestProgram

import zekell


class TestTest(unittest.TestCase):

    def test_basic(self):
        self.assertEqual('test', 'test')


class TestCreateTables(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._db_path = Path('test.db')
        cls._db = zekell.db_connection(cls._db_path, True)

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

    @classmethod
    def tearDownClass(cls) -> None:
        cls._db.conn.close()
        cls._db_path.unlink()



if __name__ == '__main__':
    unittest.main()
