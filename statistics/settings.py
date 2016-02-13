# Icecast Connection data, for icecast 2.3.2 version

"""
HOST = u'katodia.com'
PORT = u'8000'
USER = u'admin'
PASSWORD = u'gk4iI$2cngrw'
URL = u'admin/stats'
"""
HOST = u'ns331078.ip-176-31-120.eu'
PORT = u'8000'
USER = u'jjsaga'
PASSWORD = u'configuraricecastconmpdnuncaacabadeconvencerme'
SOURCE_MOUNT = u'/mpd'

URL_MAIN_STATS = u'admin/stats'
URL_LIST_CLIENTS = u'admin/listclients?mount=' + SOURCE_MOUNT

HEADERS = {
    'User-Agent': u'PodcastManager v1.0.0 (Stats retriever request) See https://github.com/sonirico/podcastmanager .'
}

HTTP_TIMEOUT = 2.0

URI_FORMAT = u'http://{}:{}/{}'

