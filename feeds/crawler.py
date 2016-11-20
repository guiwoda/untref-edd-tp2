from urllib.request import urlopen

class FeedCrawler():
    def crawl(self):

        feeds = {
            'clarin': {
                'economia': 'http://www.clarin.com/rss/ieco/',
                'mundo': 'http://www.clarin.com/rss/mundo/',
                'politica': 'http://www.clarin.com/rss/politica/',
                'sociedad': 'http://www.clarin.com/rss/sociedad/',
                'ultimas': 'http://www.clarin.com/rss/lo-ultimo/',
            },
            'el-litoral': {
                'economia': 'http://www.ellitoral.com/rss/econ.xml',
                'mundo': 'http://www.ellitoral.com/rss/inte.xml',
                'politica': 'http://www.ellitoral.com/rss/poli.xml',
                'sociedad': 'http://www.ellitoral.com/rss/soci.xml',
                'ultimas': 'http://www.ellitoral.com/rss/um.xml',
            },
            'la-voz': {
                'economia': 'http://www.lavoz.com.ar/taxonomy/term/2/1/feed',
                'mundo': 'http://www.lavoz.com.ar/taxonomy/term/5/1/feed',
                'politica': 'http://www.lavoz.com.ar/taxonomy/term/4/1/feed',
                'sociedad': 'http://www.lavoz.com.ar/taxonomy/term/6/1/feed',
                'ultimas': 'http://www.lavoz.com.ar/rss.xml',
            },
            'mendoza-online': {
                'economia': 'http://www.mdzol.com/files/rss/economia.xml',
                'mundo': 'http://www.mdzol.com/files/rss/mundo.xml',
                'politica': 'http://www.mdzol.com/files/rss/politica.xml',
                'sociedad': 'http://www.mdzol.com/files/rss/sociedad.xml',
                'ultimas': 'http://www.mdzol.com/files/rss/todoslostitulos.xml',
            },
            'telam': {
                'economia': 'http://www.telam.com.ar/rss2/economia.xml',
                'mundo': 'http://www.telam.com.ar/rss2/internacional.xml',
                'politica': 'http://www.telam.com.ar/rss2/politica.xml',
                'sociedad': 'http://www.telam.com.ar/rss2/sociedad.xml',
                'ultimas': 'http://www.telam.com.ar/rss2/ultimasnoticias.xml',
            },
        }

        encodings = {
            'clarin': 'utf-8',
            'el-litoral': 'iso-8859-1',
            'la-voz': 'utf-8',
            'mendoza-online': 'utf-8',
            'telam': 'utf-8',
        }

        # today = date.today()
        for feed, channels in feeds.items():
            for name, url in channels.items():
                with urlopen(url) as data:
                    with open('xml/%s-%s.xml' % (feed, name), 'w+') as file:
                        file.write(data.read().decode(encodings[feed]))


if __name__ == '__main__':
    FeedCrawler().crawl()