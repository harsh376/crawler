from test.basetestcase import TestCase
from crawler import crawler

# relative to /project
URLS_FILE = './test/mock_data/urls.txt'


class CrawlerTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(CrawlerTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(CrawlerTests, cls).tearDownClass()

    def setUp(self):
        self.c = crawler(self.db_conn, URLS_FILE)

    # Check to see if the URL's are being parsed correctly
    def test_url_queue(self):
        urls = self.c._url_queue
        self.assertEquals(len(urls), 3)
        self.assertEquals(urls, [
            ('https://ca.sports.yahoo.com', 0),
            ('https://ca.sports.yahoo.com/blogs', 0),
            ('https://ca.sports.yahoo.com/photos', 0),
        ])

    def test_add_link(self):
        self.c.add_link(from_doc_id=1, to_doc_id=2)
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM links;')
        data = cursor.fetchall()
        self.assertEqual(data, [(1, 2)])

    def test_update_page_ranks(self):
        self.c.crawl(depth=0)
        self.c.update_page_ranks()
        data = self.c.get_page_ranks()
        self.assertEqual(len(data), 3)

    def test_get_page_ranks(self):
        cursor = self.db_conn.cursor()
        cursor.execute('INSERT INTO page_ranks VALUES (1, 0.234)')
        cursor.execute('INSERT INTO page_ranks VALUES (2, 0.111)')
        data = self.c.get_page_ranks()
        self.assertEqual(data, [(1, 0.234), (2, 0.111)])
