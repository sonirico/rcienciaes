from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'stats/$', StatsView.as_view(), name='stats'),
    url(r'status/$', StatusView.as_view(), name='status'),
    url(r'live/$', LiveView.as_view(), name='live'),
    url(r'current/$', CurrentAudioView.as_view(), name='current'),
    url(r'current_from_metadata/$', CurrentAudioFromMetadataView.as_view(), name='current-metadata'),
    url(r'next/(?P<how_many>\d+)/$', NextView.as_view(), name='next'),
    url(r'next/$', NextView.as_view(), name='next'),
    url(r'playlist/$', PlaylistView.as_view(), name='playlist'),
]