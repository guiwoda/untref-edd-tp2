import re
import json
import nltk
from os.path import dirname, isfile
from xml.etree import ElementTree
from functools import reduce
from nltk import word_tokenize
from nltk.stem.snowball import SpanishStemmer


class Indexer(object):
    BLOCK_SIZE = 10
    TITLE_ID = 'T'
    DESCRIPTION_ID = 'D'

    def __init__(self):
        self.cwd = dirname(__file__)
        self.stopwords = self.load_stopwords()
        self.ids = self.load_json('%s/ids.json' % self.cwd)
        self.stemmer = SpanishStemmer()
        self.last_word_finder = re.compile('\d+([a-z]+)$')
        self.stemming_filter = re.compile('^[a-z]+$')
        self.index = self.load_index()
        self.dictionary = self.load_dictionary()

        nltk.data.path.append(dirname(self.cwd) + '/nltk_data')

    def load_dictionary(self):
        dictionary_path = '%s/dict.idx' % self.cwd
        if isfile(dictionary_path):
            with open(dictionary_path, 'r') as dictionary_file:
                return ''.join(dictionary_file.readlines())

    def load_index(self):
        index_path = '%s/index.json' % self.cwd
        if isfile(index_path):
            with open(index_path, 'r') as index_file:
                return json.load(index_file)

    def index(self):
        self.curr_block = 0
        self.curr_pos = 0
        self.curr_primary_pos = 0
        self.dictionary = ''

        feeds = self.load_json('%s/feeds.json' % self.cwd)

        all_items = []

        for feed, info in feeds.items():
            for channel in info['channels']:
                index = "%s-%s" % (feed, channel)
                filename = "%s/%s.xml" % (dirname(self.cwd) + '/xml', index)

                with open(filename, 'r') as xml_data:
                    data = ElementTree.parse(xml_data)

                for item in data.findall('.//item'):
                    docid = '%s%s%s' % (self.ids[feed], self.ids[channel], item.attrib['id'])
                    title = item.find('./title').text

                    description_item = item.find('./description')
                    descr = description_item.text if description_item else ''

                    all_items.append((docid, title, descr))

        self.index = reduce(self.reducer, self.map(all_items), {})

        with open('%s/index.json' % self.cwd, 'w+') as index_file:
            json.dump(self.index, index_file)

        with open('%s/dict.idx' % self.cwd, 'w+') as dictionary_file:
            dictionary_file.write(self.dictionary)

    def map(self, all_items):
        return sorted([term_doc_pair for pairs in map(self.mapper, all_items) for term_doc_pair in pairs])

    def mapper(self, item):
        (id, title, descr) = item

        return [
            (word, section, id)
            for (word, section) in
            self.stem_tokenize(title, self.TITLE_ID) + self.stem_tokenize(descr, self.DESCRIPTION_ID)
        ]

    def reducer(self, index, item):
        '''
        :type index: dict
        :type item: tuple
        :return: dict
        '''
        (term, section, id) = item

        last_term = self.get_last_term()
        dictionary_entry = str(len(term)) + term

        if term != last_term:
            self.dictionary += dictionary_entry
            self.curr_pos += len(dictionary_entry)

            if last_term:
                self.curr_block += 1
                if self.curr_block >= self.BLOCK_SIZE:
                    self.curr_block = 0
                    self.curr_primary_pos = self.curr_pos

        key = str(self.curr_primary_pos)

        # Cada palabra tendrá:
        #    "T": [
        #       0: title_freq
        #       1: title_docIDs
        #    ],
        #    "D": [
        #       0: descr_freq
        #       1: descr_docIDs
        #    ]
        index.setdefault(key, [
            {
                self.TITLE_ID: [0, []],
                self.DESCRIPTION_ID: [0, []]
            }
            for _ in range(0, self.BLOCK_SIZE)
        ])

        index[key][self.curr_block][section][0] += 1
        index[key][self.curr_block][section][1].append(id)

        return index

    def stem_tokenize(self, text, section):
        return [
            (stemmed, section) for stemmed in [
                self.stemmer.stem(word)
                for word in word_tokenize(text, 'spanish')
                if word not in self.stopwords
                and len(word) > 3
            ]
            if self.stemming_filter.match(stemmed)
        ]

    def load_json(self, filename):
        with open(filename, 'r') as file:
            return json.load(file)

    def load_stopwords(self):
        with open('%s/stopwords.txt' % self.cwd, 'r') as file:
            return set(file.readlines())

    def get_last_term(self):
        result = self.last_word_finder.search(self.dictionary)

        return result.group(1) if result else ''
