import unittest
import sqlite3


class TestCase(unittest.TestCase):

    def setUp(self):
        self.db_conn = sqlite3.connect('test.db')

    def tearDown(self):
        self.db_conn.close()
