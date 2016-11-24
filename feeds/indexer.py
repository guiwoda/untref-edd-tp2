import re
import json
import nltk
from math import floor
from os.path import dirname, isfile, abspath
from xml.etree import ElementTree
from functools import reduce
from nltk import word_tokenize
from nltk.stem.snowball import SpanishStemmer
from html import unescape
from django.utils.html import strip_tags

nltk.data.path.append(dirname(abspath(dirname(__file__))) + '/nltk_data')

class Indexer(object):
    def __init__(self):
        self.cwd = abspath(dirname(__file__))
        self.ids = self.load_json('%s/ids.json' % self.cwd)
        self.index = Index(
            stopwords=self.load_stopwords(),
            ids=self.ids
        )

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
                    title = unescape(item.find('./title').text)
                    descr = ''

                    descr_item = item.find('./description')
                    if descr_item is not None:
                        descr = unescape(str(descr_item.text))

                    all_items.append((docid, title, descr))

        self.index.add(all_items)
        self.index.save_to(dirname(self.cwd) + '/tmp')

    def load_json(self, filename):
        with open(filename, 'r') as file:
            return json.load(file)

    def load_stopwords(self):
        with open('%s/stopwords.txt' % self.cwd, 'r') as file:
            return set(file.readlines())

    def load_index(self):
        self.index.load_from(dirname(self.cwd)+'/tmp')

        return self.index


class Index():
    BLOCK_SIZE = 10
    TITLE_SECTION = 'T'
    DESCRIPTION_SECTION = 'D'
    DICTIONARY_FILENAME = 'dict.idx'
    AUX_FILENAME = 'aux.json'

    curr_block = 0
    curr_pos = 0
    curr_primary_pos = 0
    dictionary = ''
    aux = {}
    aux_feeds = {}
    aux_channels = {}
    aux_feeds_channels = {}
    aux_keys = []
    loaded_xmls = {}
    last_term = ''

    def __init__(self, stopwords=None, stemmer=SpanishStemmer(), ids=None):
        self.stemmer = stemmer
        self.stopwords = stopwords if stopwords else set()
        self.ids = ids if ids else {}

        self.last_word_finder = re.compile('\d+([a-z]+)$')
        self.stemming_filter = re.compile('^[a-z]+$')
        self.all_numbers = re.compile('^\d+$')

    def reducer(self, index, item):
        '''
        :type index: dict
        :type item: tuple
        :return: dict
        '''
        (term, section, docid) = item
        feed_id = docid[0:2]
        channel_id = docid[2:4]
        feed_channel_id = docid[0:4]

        self.aux_feeds.setdefault(feed_id, {})
        self.aux_channels.setdefault(channel_id, {})
        self.aux_feeds_channels.setdefault(feed_channel_id, {})

        last_term = self.get_last_term()
        dictionary_entry = str(len(term)) + term

        if term != last_term:
            self.dictionary += dictionary_entry

            if last_term:
                self.curr_pos += len(str(len(last_term)) + last_term)

                self.curr_block += 1
                if self.curr_block >= self.BLOCK_SIZE:
                    self.curr_block = 0
                    self.curr_primary_pos = self.curr_pos

            self.last_term = term

        key = str(self.curr_primary_pos)
        print(term, last_term, section, docid, key, self.curr_primary_pos, self.curr_block, self.curr_pos)

        index.setdefault(key, self.get_default_index_structure())
        self.aux_feeds[feed_id].setdefault(key, self.get_default_index_structure())
        self.aux_channels[channel_id].setdefault(key, self.get_default_index_structure())
        self.aux_feeds_channels[feed_channel_id].setdefault(key, self.get_default_index_structure())

        index[key][self.curr_block][section][0] += 1
        index[key][self.curr_block][section][1].append(docid)
        self.aux_feeds[feed_id][key][self.curr_block][section][0] += 1
        self.aux_feeds[feed_id][key][self.curr_block][section][1].append(docid)
        self.aux_channels[channel_id][key][self.curr_block][section][0] += 1
        self.aux_channels[channel_id][key][self.curr_block][section][1].append(docid)
        self.aux_feeds_channels[feed_channel_id][key][self.curr_block][section][0] += 1
        self.aux_feeds_channels[feed_channel_id][key][self.curr_block][section][1].append(docid)

        return index

    def get_default_index_structure(self):
        '''
        Cada palabra tendrá:
           "T": [
              0: title_freq
              1: title_docIDs
           ],
           "D": [
              0: descr_freq
              1: descr_docIDs
           ]
        :return: list
        '''

        return [
            {
                self.TITLE_SECTION: [0, []],
                self.DESCRIPTION_SECTION: [0, []]
            }
            for _ in range(0, self.BLOCK_SIZE)
        ].copy()

    def map(self, all_items):
        return sorted([term_doc_pair for pairs in map(self.mapper, all_items) for term_doc_pair in pairs])

    def mapper(self, item):
        (docid, title, descr) = item

        return [
            (word, section, docid)
            for (word, section) in
            self.stem_tokenize(title, self.TITLE_SECTION) +
            self.stem_tokenize(descr, self.DESCRIPTION_SECTION)
            ]

    def stem_tokenize(self, text, section):
        return [
            (stemmed, section) for stemmed in [
                self.stemmer.stem(word)
                for word in word_tokenize(strip_tags(text), 'spanish')
                if word not in self.stopwords
                and len(word) > 3
                ]
            if self.stemming_filter.match(stemmed)
            ]

    def get_last_term(self):
        return self.last_term if self.last_term else ''

    def add(self, items):
        self.set_aux(reduce(self.reducer, self.map(items), {}))

    def load_from(self, directory):
        dictionary_path = '%s/%s' % (directory, self.DICTIONARY_FILENAME)
        if isfile(dictionary_path):
            with open(dictionary_path, 'r') as dictionary_file:
                self.dictionary = ''.join(dictionary_file.readlines())

        aux_path = '%s/%s' % (directory, self.AUX_FILENAME)
        if isfile(aux_path):
            with open(aux_path, 'r') as aux_file:
                self.set_aux(json.load(aux_file))

        path = '%s/feeds_%s' % (directory, self.AUX_FILENAME)
        if isfile(path):
            with open(path, 'r') as aux_file:
                self.aux_feeds = json.load(aux_file)

        path = '%s/channels_%s' % (directory, self.AUX_FILENAME)
        if isfile(path):
            with open(path, 'r') as aux_file:
                self.aux_channels = json.load(aux_file)

        path = '%s/channels_feeds_%s' % (directory, self.AUX_FILENAME)
        if isfile(path):
            with open(path, 'r') as aux_file:
                self.aux_feeds_channels = json.load(aux_file)

    def save_to(self, directory):
        with open('%s/%s' % (directory, self.AUX_FILENAME), 'w') as aux_file:
            json.dump(self.aux, aux_file)

        with open('%s/feeds_%s' % (directory, self.AUX_FILENAME), 'w') as aux_file:
            json.dump(self.aux_feeds, aux_file)

        with open('%s/channels_%s' % (directory, self.AUX_FILENAME), 'w') as aux_file:
            json.dump(self.aux_channels, aux_file)

        with open('%s/channels_feeds_%s' % (directory, self.AUX_FILENAME), 'w') as aux_file:
            json.dump(self.aux_feeds_channels, aux_file)

        with open('%s/%s' % (directory, self.DICTIONARY_FILENAME), 'w') as dictionary_file:
            dictionary_file.write(self.dictionary)

    def boolean_search(self, phrase):
        phrase = phrase.strip()

        terms = list(map(lambda term: term.strip(), re.split('(and|or)', phrase)))

        if not terms:
            return {}

        results = self.single_term_search(terms[0])
        for term in terms[1:]:
            if term == 'and':
                right = self.single_term_search(terms[terms.index(term) + 1])
                results = [result for result in results if result in right]
            elif term == 'or':
                right = self.single_term_search(terms[terms.index(term) + 1])
                results = results + right
            # elif term == 'not':
            #     right = self.single_term_search(terms[terms.index(term) + 1])
            #     if right:
            #         results = [result for result in results if result not in right]

        return list(set(results))

    def single_term_search(self, term):
        if ' ' in term:
            results = self.boolean_search(' and '.join(term.split()))

            return filter(lambda docid: self.article_contains_term(docid, term), results)

        result = self.search(term)

        if not result:
            return []

        return result[self.TITLE_SECTION][1] + result[self.DESCRIPTION_SECTION][1]

    def article_contains_term(self, docid, term):
        link, title, description = self.get_article_by_id(docid)

        return term in title or term in description

    def search(self, word):
        return self.binary_search(self.stemmer.stem(word))

    def binary_search(self, word, min=0, max=None):
        max = max if max is not None else len(self.aux_keys)

        if max < min:
            return None

        mid = int(min + floor((max - min) / 2))
        print(min, mid, max)
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

    def ranking_title(self, n=10, feed=None, channel=None):
        return self.ranking(self.TITLE_SECTION, n, feed, channel)

    def ranking_description(self, n=10, feed=None, channel=None):
        return self.ranking(self.DESCRIPTION_SECTION, n, feed, channel)

    def ranking(self, section, limit, feed, channel):
        aux = self.aux

        if feed:
            if channel:
                aux = self.aux_feeds_channels[self.ids[feed] + self.ids[channel]]
            else:
                aux = self.aux_feeds[self.ids[feed]]
        elif channel:
            aux = self.aux_channels[self.ids[channel]]

        sorted_aux = sorted(aux, reverse=True, key=lambda k: max(
            aux[k],
            key=lambda word_data: word_data[section][0])[section][0]
        )

        words = []
        for i in range(0, 10):
            key = sorted_aux[i]
            end = int(key)

            for j in range(0, self.BLOCK_SIZE):
                (word, end) = self.get_from_dictionary(end)
                words.append([word] + aux[key][j][section])

        words = sorted(words, reverse=True, key=lambda tpl: tpl[1])

        return words[0:limit]

    def get_article_by_id(self, article_id):
        ids = {v: k for k, v in self.ids.items()}
        feed = article_id[0:2]
        channel = article_id[2:4]
        doc_id = article_id[4:]

        data = self.load_xml(channel, feed, ids)

        item = data.find('.//item[@id="%s"]' % doc_id)

        link = item.findtext('./link', '').strip()
        title = item.findtext('./title', '').strip()
        descr = item.findtext('./description', '').strip()

        return link, title, descr

    def load_xml(self, channel, feed, ids):
        cwd = abspath(dirname(__file__))
        filename = "%s/%s-%s.xml" % (dirname(cwd) + '/xml', ids[feed], ids[channel])

        if filename not in self.loaded_xmls:
            with open(filename, 'r') as xml_data:
                self.loaded_xmls[filename] = ElementTree.parse(xml_data)

        return self.loaded_xmls[filename]


if __name__ == '__main__':
    indexer = Indexer()
    indexer.run_index()
