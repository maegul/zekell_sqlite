from pathlib import Path
import unittest

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

    @classmethod
    def tearDownClass(cls) -> None:
        cls._db.conn.close()
        cls._db_path.unlink()


if __name__ == '__main__':
    unittest.main()
