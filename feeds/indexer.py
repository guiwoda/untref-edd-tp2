import json
import nltk
from os.path import dirname
from xml.etree import ElementTree
from functools import reduce
from nltk import word_tokenize
from nltk.stem.snowball import SpanishStemmer


class Indexer():
    def __init__(self):
        self.stopwords = self.load_stopwords()
        self.stemmer = SpanishStemmer()
        nltk.data.path.append(dirname(dirname(__file__)) + '/nltk_data')

    def index(self):
        cwd = dirname(__file__)
        with open('%s/feeds.json' % cwd, 'r') as feeds_data:
            with open('%s/indexed.json' % cwd, 'rw') as indexed_data:

                feeds = json.load(feeds_data)
                indexed = json.load(indexed_data)

                for feed, info in feeds.items():
                    for channel in info['channels']:
                        index = "%s-%s" % (feed, channel)
                        filename = "%s/%s.xml" % (cwd, index)

                        with open(filename, 'r') as xml_data:
                            data = ElementTree.parse(xml_data)

                            for item in data.findall('.//item'):
                                if not item.attrib['id'] in indexed[index]:
                                    self.add_title_to_index(item.attrib['id'], item.find('./title').text)

    def add_title_to_index(self, id, title):
        occurrences = {}

        def reducer(id, word):
            occurrences.setdefault(word, {
                'freq': 0,
                'docs': []
            })

            occurrences[word]['freq'] += 1
            occurrences[word]['docs'].append(id)

        return reduce(reducer, map(lambda word: (id, word), self.parse_title(title)))

    def parse_title(self, title):
        return {
            self.stemmer.stem(word)
            for word in word_tokenize(title, 'spanish')
            if word not in self.stopwords
            and len(word) > 3
        }

    def load_stopwords(self):
        cwd = dirname(__file__)

        with open('%s/stopwords.txt' % cwd, 'r') as file:
            return set(file.readlines())

