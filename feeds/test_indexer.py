import unittest

from feeds.indexer import Index, Indexer


class TestIndexer(unittest.TestCase):
    def testAddsWordsToAnIndex(self):
        index = Index()
        index.add([('DCID123', 'Palabra', 'Frase')])

        result = index.search('Palabra')

        self.assertNotEqual(None, result)
        self.assertIn('DCID123', result[Index.TITLE_SECTION][1])
        self.assertNotIn('DCID123', result[Index.DESCRIPTION_SECTION][1])

        result = index.search('Frase')

        self.assertNotEqual(None, result)
        self.assertIn('DCID123', result[Index.DESCRIPTION_SECTION][1])
        self.assertNotIn('DCID123', result[Index.TITLE_SECTION][1])
