from test.basetestcase import TestCase
from crawler import crawler


# relative to /project
URLS_FILE = './test/mock_data/testurls.txt'


class InvertedIndexTests(TestCase):

    # Initialize db connection, run the crawler once before the tests begin
    @classmethod
    def setUpClass(cls):
        super(InvertedIndexTests, cls).setUpClass()
        cls.bot = crawler(cls.db_conn, URLS_FILE)
        cls.bot.crawl(depth=0)
        cls.temp_resolved_index = cls.bot.get_resolved_inverted_index()

    # Close db connection
    @classmethod
    def tearDownClass(cls):
        super(InvertedIndexTests, cls).tearDownClass()

    # Test to see if the number of words parsed in the given url is correct
    def test_get_resolved_index(self):
        self.assertEqual(
            len(self.temp_resolved_index),
            2,
            'Number of Keys != 2. Incorrect Value',
        )
        expected_data = {
            'verma': {'http://www.harshverma.com/'},
            'harsh': {'http://www.harshverma.com/'},
        }
        self.assertEqual(self.temp_resolved_index, expected_data)
