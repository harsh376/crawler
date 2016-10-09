from test.basetestcase import TestCase
from crawler import crawler

class InvertedIndexTests(TestCase):

	# Test to see if the number of words parsed in the given url is correct
	def test_resolved_index_size(self):
		self.assertEqual(len(self.temp_resolved_index), 2, 'Number of Keys != 2. Incorrect Value')

    # Test to see if the words parsed are correct
	def test_keys_in_resolved_index(self):
		foundKeys = ('harsh' in self.temp_resolved_index) and ('verma' in self.temp_resolved_index)
		self.assertTrue(foundKeys, 'Words found do not match actual words in the document')
	

