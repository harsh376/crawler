import unittest


class TestCase(unittest.TestCase):
    def setUp(self):
        print('setup')

    def tearDown(self):
        print('teardown')

if __name__ == '__main__':
    unittest.main()
