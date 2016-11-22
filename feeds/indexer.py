import re
import json
import nltk
from math import floor
from os.path import dirname, isfile, abspath
from xml.etree import ElementTree
from functools import reduce
from nltk import word_tokenize
from nltk.stem.snowball import SpanishStemmer


class Indexer(object):
    def __init__(self):
        self.cwd = abspath(dirname(__file__))
        self.ids = self.load_json('%s/ids.json' % self.cwd)

        nltk.data.path.append(dirname(self.cwd) + '/nltk_data')

    def run_index(self):
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

        self.index = Index(
            stopwords=self.load_stopwords()
        )
        self.index.add(all_items)
        self.index.save_to(self.cwd)

    def load_json(self, filename):
        with open(filename, 'r') as file:
            return json.load(file)

    def load_stopwords(self):
        with open('%s/stopwords.txt' % self.cwd, 'r') as file:
            return set(file.readlines())


class Index():
    BLOCK_SIZE = 10
    TITLE_ID = 'T'
    DESCRIPTION_ID = 'D'
    DICTIONARY_FILENAME = 'dict.idx'
    AUX_FILENAME = 'aux.json'

    curr_block = 0
    curr_pos = 0
    curr_primary_pos = 0
    dictionary = ''
    aux = {}
    aux_keys = []

    def __init__(self, stopwords=None, stemmer=SpanishStemmer()):
        self.stemmer = stemmer
        self.stopwords = stopwords if stopwords is not None else set()

        self.last_word_finder = re.compile('\d+([a-z]+)$')
        self.stemming_filter = re.compile('^[a-z]+$')
        self.all_numbers = re.compile('^\d+$')

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

    def map(self, all_items):
        return sorted([term_doc_pair for pairs in map(self.mapper, all_items) for term_doc_pair in pairs])

    def mapper(self, item):
        (id, title, descr) = item

        return [
            (word, section, id)
            for (word, section) in
            self.stem_tokenize(title, self.TITLE_ID) + self.stem_tokenize(descr, self.DESCRIPTION_ID)
            ]

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

    def get_last_term(self):
        result = self.last_word_finder.search(self.dictionary)

        return result.group(1) if result else ''

    def add(self, items):
        self.set_aux(reduce(self.reducer, self.map(items), self.aux))

    def load_from(self, directory):
        dictionary_path = '%s/%s' % (directory, self.DICTIONARY_FILENAME)
        if isfile(dictionary_path):
            with open(dictionary_path, 'r') as dictionary_file:
                self.dictionary = ''.join(dictionary_file.readlines())

        aux_path = '%s/%s' % (directory, self.AUX_FILENAME)
        if isfile(aux_path):
            with open(aux_path, 'r') as aux_file:
                self.set_aux(json.load(aux_file))

    def save_to(self, directory):
        with open('%s/%s' % (directory, self.AUX_FILENAME), 'w+') as aux_file:
            json.dump(self.aux, aux_file)

        with open('%s/%s' % (directory, self.DICTIONARY_FILENAME), 'w+') as dictionary_file:
            dictionary_file.write(self.dictionary)

    def search(self, word):
        return self.binary_search(self.stemmer.stem(word))

    def binary_search(self, word, min=0, max=None):
        max = max if max is not None else len(self.aux_keys)

        if max < min:
            return None

        mid = int(min + floor((max - min) / 2))
        key = self.aux_keys[mid]
        (candidate, end) = self.get_from_dictionary(key)

        if word == candidate:
            return self.aux[str(key)][0]
        if word < candidate:
            return self.binary_search(word, min, mid - 1)

        for i in range(1, self.BLOCK_SIZE):
            (candidate, end) = self.get_from_dictionary(end)

            if word == candidate:
                return self.aux[str(key)][i]

        return self.binary_search(word, mid + 1, max)

    def set_aux(self, aux):
        self.aux = aux
        self.aux_keys = sorted(map(int, list(self.aux.keys())))

    def get_from_dictionary(self, key):
        chars = self.dictionary[key]
        start = key + 1

        # Soportar dos dígitos
        if self.all_numbers.match(self.dictionary[key:start + 1]):
            chars = self.dictionary[key:start + 1]
            start += 1

        end = start + int(chars)

        return self.dictionary[start:end], end

    def ranking_title(self):
        return self.ranking(self.TITLE_ID)

    def ranking_description(self):
        return self.ranking(self.DESCRIPTION_ID)

    def ranking(self, section):
        sorted_aux = sorted(self.aux, reverse=True, key=lambda k: max(self.aux[k], key=lambda word_data: word_data[section][0])[section][0])

        words = []
        for i in range(0, 10):
            key = sorted_aux[i]
            end = int(key)

            for j in range(0, self.BLOCK_SIZE):
                (word, end) = self.get_from_dictionary(end)
                words.append([word] + self.aux[key][j][section])

        words = sorted(words, reverse=True, key=lambda tpl: tpl[1])

        return words[0:10]

if __name__ == '__main__':
    indexer = Indexer()
    indexer.run_index()
