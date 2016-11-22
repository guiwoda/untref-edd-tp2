from django.shortcuts import render
from django.http import HttpResponse

from feeds.indexer import Indexer


def index(request):
    indexer = Indexer()
    index = indexer.load_index()

    feeds = {
        "Clarin": "clarin",
        "El litoral": "el-litoral",
        "La voz del Interior": "la-voz",
        "Mendoza Online": "mendoza-online",
        "Telam": "telam",
    }

    channels = {
        "Economia": "economia",
        "Mundo": "mundo",
        "Politica": "politica",
        "Sociedad": "sociedad",
        "Ultimas": "ultimas",
    }

    # def for_all_articles(word, freq, arts, fn):
    #     return word, freq, map(fn, arts)

    query = request.GET.get('q')

    # if query:
    #     results = index.search(query)
    # else:
    results = index.ranking_title(feed=request.GET.get('feed'), channel=request.GET.get('channel'))

    articles = map(lambda words: (words[0], words[1], map(index.get_article_by_id, words[2])), results)


    return render(request, 'news/index.html', {
        'feeds': feeds.items(),
        'channels': channels.items(),
        'words': articles,
    })
