from test.basetestcase import TestCase
from crawler import crawler

# relative to /project
URLS_FILE1 = './test/mock_data/urls.txt'
URLS_FILE2 = './test/mock_data/testurls.txt'


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
        cursor.execute('INSERT INTO page_ranks VALUES (1, 0.234)')
        cursor.execute('INSERT INTO page_ranks VALUES (2, 0.111)')
        data = c.get_page_ranks()
        self.assertEqual(data, [(1, 0.234), (2, 0.111)])

    def test_get_resolved_index(self):
        c = crawler(self.db_conn, URLS_FILE2)
        c.crawl(depth=0)
        resolved_inverted_index = c.get_resolved_inverted_index()
        self.assertEqual(
            len(resolved_inverted_index),
            2,
            'Number of Keys != 2. Incorrect Value',
        )
        expected_data = {
            'verma': {'http://www.harshverma.com/'},
            'harsh': {'http://www.harshverma.com/'},
        }
        self.assertEqual(resolved_inverted_index, expected_data)

    def test_get_inverted_index(self):
        pass

    def test_update_inverted_index(self):
        pass

    def test_insert_word_in_lexicon(self):
        pass

    def test_insert_doc_in_doc_index(self):
        pass

    def test_word_id(self):
        pass

    def test_document_id(self):
        pass
