from urllib.request import urlopen
from os.path import dirname, isfile
import json
from xml.etree import ElementTree


class FeedCrawler(object):
    def crawl(self):
        with open(dirname(__file__) + '/feeds.json', 'r') as config:
            feeds = json.loads("\n".join(config.readlines()))

            for feed, info in feeds.items():
                for name, url in info['channels'].items():
                    self.crawl_feed(feed, name, url)

    def crawl_feed(self, name, channel, url):
        with urlopen(url) as data:
            filename = 'xml/%s-%s.xml' % (name, channel)
            elements = ElementTree.parse(data)

            if not isfile(filename):
                print("> No existe el archivo %s" % filename)

                self.new_feed_file(filename, elements)
            else:
                print("> Usando %s" % filename)

                self.append_to_feed_file(filename, elements)

    def new_feed_file(self, filename, elements):
        lastId = 0

        for element in elements.findall('.//item'):
            lastId += 1
            element.attrib['id'] = str(lastId)

            print(">> Agrego noticia %s a %s" % (element.find('title').text, filename))

        elements.write(filename)

    def append_to_feed_file(self, filename, elements):
        modified = False
        current = ElementTree.parse(filename)
        last_id = self.find_last_id(current)

        for element in elements.findall('.//item'):
            link = element.find('link').text

            if not current.findall('.//item[link="%s"]' % link):
                last_id += 1

                element.attrib['id'] = str(last_id)
                current.find('./channel').append(element)

                print(">> Agrego noticia id(%i): %s a %s" % (last_id, element.find('title').text, filename))
                modified = True

        if modified:
            current.write(filename)

    def find_last_id(self, elements):
        last_id = 0

        for item in elements.findall('.//item'):
            curr_id = int(item.attrib['id'])

            if curr_id > last_id:
                last_id = curr_id

        return last_id

if __name__ == '__main__':
    FeedCrawler().crawl()
