from test.basetestcase import TestCase
from crawler import crawler

# relative to /project
URLS_FILE = './test/mock_data/urls.txt'


class SomethingTestCase(TestCase):

    def test_url_queue(self):
        c = crawler(None, URLS_FILE)
        urls = c._url_queue
        self.assertEquals(len(urls), 3)
        self.assertEquals(urls, [
            ('http://www.a.com', 0),
            ('http://www.b.com', 0),
            ('http://www.c.com', 0),
        ])
