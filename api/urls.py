from django.conf.urls import patterns
from api import views

urlpatterns = patterns('',
    (r'current/$', views.current),
    (r'live/$', views.live),
    (r'status/$', views.status),
    (r'playlistinfo/$', views.playlistinfo),
    (r'song_by_pos/(?P<song_pos>\d+)$', views.get_song_by_pos),
    (r'song_by_id/(?P<song_id>\d+)$', views.get_song_by_id),
    (r'podcast/$', views.podcast),
    (r'next/$', views.next_podcast),
    (r'playlist/$', views.playlist),
    (r'podcastbyid/(?P<podcast_id>\d+)/$', views.podcast_by_id),
)
