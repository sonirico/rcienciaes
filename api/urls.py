from django.conf.urls import url
from api import views
from api.views import AudioListView
from .views import *

urlpatterns = [
    url(r'current/$', views.current, name='current'),
    url(r'live/$', views.live, name='live'),
    url(r'stats/$', views.stats, name='stats'),
    #url(r'status/$', views.status, name='status'),
    url(r'playlistinfo/$', views.playlistinfo),
    url(r'song_by_pos/(?P<song_pos>\d+)$', views.get_song_by_pos),
    url(r'song_by_id/(?P<song_id>\d+)$', views.get_song_by_id),
    url(r'podcast/$', views.podcast, name='podcast'),
    url(r'next/$', views.next_podcast),
    url(r'playlist/$', views.playlist),
    url(r'podcastbyid/(?P<podcast_id>\d+)/$', views.podcast_by_id),
    url(r'audios/', AudioListView.as_view()),

    url(r'status/$', StatusView.as_view(), name='status'),
]