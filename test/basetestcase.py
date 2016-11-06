import unittest
import sqlite3


class TestCase(unittest.TestCase):

    db_conn = None

    @classmethod
    def setUpClass(cls):
        cls.db_conn = sqlite3.connect('test.db')

    @classmethod
    def tearDownClass(cls):
        cls.db_conn.close()

    def setUp(self):
        pass

    def tearDown(self):
        pass
