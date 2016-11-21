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
        self.ids = {
            'clarin':         'CL',
            'el-litoral':     'LI',
            'la-voz':         'VZ',
            'mendoza-online': 'MO',
            'telam':          'TM',
            'economia':       'EC',
            'mundo':          'MU',
            'politica':       'PO',
            'sociedad':       'SO',
            'ultimas':        'UL',
        }

    def index(self):
        cwd = dirname(__file__)
        with open('%s/feeds.json' % cwd, 'r') as feeds_data:
            feeds = json.load(feeds_data)
            current_index = {}

            for feed, info in feeds.items():
                for channel in info['channels']:
                    index = "%s-%s" % (feed, channel)
                    filename = "%s/%s.xml" % (dirname(cwd) + '/xml', index)

                    with open(filename, 'r') as xml_data:
                        data = ElementTree.parse(xml_data)

                        for item in data.findall('.//item'):
                            self.add_title_to_index(
                                '%s%s%s' % (self.ids[feed], self.ids[channel], item.attrib['id']),
                                item.find('./title').text,
                                current_index
                            )

                with open('%s/index.json' % cwd, 'w+') as index_file:
                    json.dump(current_index, index_file)

    def add_title_to_index(self, id, title, index):
        def reducer(carry, item):
            (id, word) = item
            carry.setdefault(word, {
                'freq': 0,
                'docs': []
            })

            carry[word]['freq'] += 1
            carry[word]['docs'].append(id)

            return carry

        return reduce(reducer, map(lambda word: (id, word), self.parse_title(title)), index)

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
