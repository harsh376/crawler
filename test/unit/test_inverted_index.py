from test.basetestcase import TestCase
from crawler import crawler


class InvertedIndexTests(TestCase):

    # Set Up is called by all tests, so run the crawler and save the
    # resolved index for later use
    def setUp(self):
        self.bot = crawler(None, "./test/mock_data/testurls.txt")
        self.bot.crawl(depth=0)
        self.temp_resolved_index = self.bot.get_resolved_inverted_index()

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
