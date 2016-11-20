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
                    with urlopen(url) as data:
                        filename = 'xml/%s-%s.xml' % (feed, name)
                        newOrModified = False

                        elements = ElementTree.parse(data)
                        lastId = 0

                        if not isfile(filename):
                            print("> No existe el archivo %s" % filename)
                            newOrModified = True
                            current = elements

                            for element in current.findall('.//item'):
                                lastId += 1

                                element.attrib['id'] = str(lastId)
                                print(">> Agrego noticia %s a %s" % (element.find('title').text, filename))
                        else:
                            print("> Usando %s" % filename)

                            current = ElementTree.parse(filename)
                            for item in current.findall('.//item'):
                                id = int(item.attrib['id'])

                                if id > lastId:
                                    lastId = id

                            for element in elements.findall('.//item'):
                                link = element.find('link').text

                                if not current.findall('.//item[link="%s"]' % link):
                                    lastId += 1

                                    element.attrib['id'] = str(lastId)
                                    current.find('./channel').append(element)

                                    print(">> Agrego noticia id(%i): %s a %s" % (lastId, element.find('title').text, filename))
                                    newOrModified = True

                        if newOrModified:
                            current.write(filename)

if __name__ == '__main__':
    FeedCrawler().crawl()
