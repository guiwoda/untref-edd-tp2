import unittest

from feeds.indexer import Indexer


class TestIndexer(unittest.TestCase):
    def testAddsWordsToAnIndex(self):
        indexer = Indexer()
        index = {}

        indexer.add_title_to_index('some_id', 'Palabra', index)

        self.assertIn('palabr', index)
        self.assertEqual(1, index['palabr']['freq'])
        self.assertIn('some_id', index['palabr']['docs'])

    def testAddsMoreWordsToAnIndex(self):
        indexer = Indexer()
        index = {
            'palabr': {
                'freq': 5,
                'docs': ['a', 'b', 'c']
            }
        }

        indexer.add_title_to_index('some_id', 'Palabra palabras', index)

        self.assertEqual(7, index['palabr']['freq'], index)
        self.assertIn('some_id', index['palabr']['docs'])