from urllib.request import urlopen
from os.path import dirname
import json


class FeedCrawler(object):
    def crawl(self):
        with open(dirname(__file__) + '/feeds.json', 'r') as config:
            feeds = json.loads("\n".join(config.readlines()))

            for feed, info in feeds.items():
                for name, url in info['channels'].items():
                    with urlopen(url) as data:
                        with open('xml/%s-%s.xml' % (feed, name), 'w+') as file:
                            file.write(data.read().decode(info['encoding']))

if __name__ == '__main__':
    FeedCrawler().crawl()
