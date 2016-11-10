from test.basetestcase import TestCase
from crawler import crawler

# relative to /project
URLS_FILE1 = './test/mock_data/urls.txt'


class CrawlerTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(CrawlerTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(CrawlerTests, cls).tearDownClass()

    # Check to see if the URL's are being parsed correctly
    def test_url_queue(self):
        c = crawler(self.db_conn, URLS_FILE1)
        urls = c._url_queue
        self.assertEquals(len(urls), 3)
        self.assertEquals(urls, [
            ('https://ca.sports.yahoo.com', 0),
            ('https://ca.sports.yahoo.com/blogs', 0),
            ('https://ca.sports.yahoo.com/photos', 0),
        ])

    def test_add_link(self):
        c = crawler(self.db_conn, URLS_FILE1)
        c.add_link(from_doc_id=1, to_doc_id=2)
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM links;')
        data = cursor.fetchall()
        self.assertEqual(data, [(1, 2)])

    def test_update_page_ranks(self):
        c = crawler(self.db_conn, URLS_FILE1)
        c.crawl(depth=0)
        c.update_page_ranks()
        data = c.get_page_ranks()
        self.assertEqual(len(data), 3)

    def test_get_page_ranks(self):
        c = crawler(self.db_conn, URLS_FILE1)
        cursor = self.db_conn.cursor()
        cursor.execute('INSERT INTO page_ranks VALUES(1, 0.234)')
        cursor.execute('INSERT INTO page_ranks VALUES(2, 0.111)')
        data = c.get_page_ranks()
        self.assertEqual(data, [(1, 0.234), (2, 0.111)])

    def test_get_resolved_index(self):
        c = crawler(self.db_conn, URLS_FILE1)
        cursor = self.db_conn.cursor()
        cursor.executescript(
            """
            INSERT INTO lexicon(id, word) VALUES(1, 'One');
            INSERT INTO lexicon(id, word) VALUES(2, 'Two');

            INSERT INTO doc_index(id, url) VALUES(2, 'http://www.google.com');
            INSERT INTO doc_index(id, url) VALUES(3, 'http://www.yahoo.com');

            INSERT INTO inverted_index(word_id, doc_id) VALUES(1, 2);
            INSERT INTO inverted_index(word_id, doc_id) VALUES(1, 3);
            INSERT INTO inverted_index(word_id, doc_id) VALUES(2, 3);
            """
        )
        data = c.get_resolved_inverted_index()
        self.assertEqual(data, {
            'One': {'http://www.google.com', 'http://www.yahoo.com'},
            'Two': {'http://www.yahoo.com'},
        })

    def test_get_inverted_index(self):
        c = crawler(self.db_conn, URLS_FILE1)
        cursor = self.db_conn.cursor()
        cursor.executescript(
            """
            INSERT INTO inverted_index(word_id, doc_id) VALUES(1, 2);
            INSERT INTO inverted_index(word_id, doc_id) VALUES(1, 3);
            INSERT INTO inverted_index(word_id, doc_id) VALUES(2, 3);
            """
        )
        data = c.get_inverted_index()
        self.assertEqual(data, {
            1: {2, 3},
            2: {3},
        })

    def test_update_inverted_index(self):
        c = crawler(self.db_conn, URLS_FILE1)
        c.update_inverted_index(1, 2)
        # try inserting duplicate, should replace
        c.update_inverted_index(1, 2)
        c.update_inverted_index(1, 3)
        c.update_inverted_index(2, 3)

        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM inverted_index')
        data = cursor.fetchall()
        self.assertEqual(data, [(1, 2), (1, 3), (2, 3)])

    def test_insert_word_in_lexicon(self):
        c = crawler(self.db_conn, URLS_FILE1)
        word = 'One'

        c.insert_word_in_lexicon(word=word)
        # Trying to insert a duplicate, should replace
        word_id = c.insert_word_in_lexicon(word=word)

        # Fetching all rows for the given word; Ensure no duplicates
        cursor = self.db_conn.cursor()
        cursor.execute(
            """SELECT * FROM lexicon WHERE id='%s';""" % word_id
        )
        data = cursor.fetchall()
        self.assertEqual(data, [(word_id, word)])

    def test_insert_doc_in_doc_index(self):
        c = crawler(self.db_conn, URLS_FILE1)
        url = 'http://www.google.com'

        c.insert_doc_in_doc_index(url=url)
        # Trying to insert a duplicate, should replace
        doc_id = c.insert_doc_in_doc_index(url=url)

        # Fetching all rows for the given url; Ensure no duplicates
        cursor = self.db_conn.cursor()
        cursor.execute(
            """SELECT * FROM doc_index WHERE id='%s';""" % doc_id
        )
        data = cursor.fetchall()
        self.assertEqual(data, [(doc_id, url)])

    def test_word_id(self):
        # setup
        cursor = self.db_conn.cursor()
        c = crawler(self.db_conn, URLS_FILE1)
        doc_id = c.insert_doc_in_doc_index('http://www.google.com')
        c._curr_doc_id = doc_id

        word = 'One'
        word_id = c.word_id(word=word)

        # Checking if word was correctly inserted into the lexicon
        cursor.execute(
            """SELECT * FROM lexicon WHERE id='%s';""" % word_id
        )
        data = cursor.fetchall()
        self.assertEqual(data, [(word_id, word)])

        # Checking if word correctly inserted into inverted_index
        data = c.get_inverted_index()
        self.assertEqual(data, {
            word_id: {doc_id},
        })

    def test_document_id(self):
        c = crawler(self.db_conn, URLS_FILE1)
        url = 'http://www.google.com'

        c.document_id(url=url)
        # Trying to insert a duplicate
        doc_id = c.document_id(url=url)

        # Fetching all rows for the given url; Ensure no duplicates
        cursor = self.db_conn.cursor()
        cursor.execute(
            """SELECT * FROM doc_index WHERE id='%s';""" % doc_id
        )
        data = cursor.fetchall()
        self.assertEqual(data, [(doc_id, url)])
