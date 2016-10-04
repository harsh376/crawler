import unittest
from crawler import crawler

class BackEndTests(unittest.TestCase):
	# Set Up is called by all tests, so run the crawler and save the
	# resolved index for later use
	def setUp(self):
		self.bot = crawler(None, "testurls.txt")
		self.bot.crawl(depth=0)
		self.temp_resolved_index = self.bot.get_resolved_index()
		print self.temp_resolved_index

	# Test to see if the number of words parsed in the given url is correct
	def test_resolved_index_size(self):
		self.assertEqual(len(self.temp_resolved_index), 2, 'Number of Keys != 2. Incorrect Value')

	# Test to see if the words parsed are correct
	def test_keys_in_resolved_index(self):
		foundKeys = ('harsh' in self.temp_resolved_index) and ('verma' in self.temp_resolved_index)
		self.assertTrue(foundKeys, 'Words found do not match actual words in the document')
		

suite = unittest.TestLoader().loadTestsFromTestCase(BackEndTests)
unittest.TextTestRunner(verbosity=2).run(suite)