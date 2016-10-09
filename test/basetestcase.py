import unittest
from crawler import crawler 

class TestCase(unittest.TestCase):

    # Set Up is called by all tests, so run the crawler and save the
	# resolved index for later use
    def setUp(self):
		self.bot = crawler(None, "./test/mock_data/testurls.txt")
		self.bot.crawl(depth=0)
		self.temp_resolved_index = self.bot.get_resolved_inverted_index()
		print self.temp_resolved_index

    def tearDown(self):
        pass

#if __name__ == '__main__':
#    unittest.main()
