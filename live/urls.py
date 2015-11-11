from django.conf.urls import url
from .views import *


urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
]

'''
    url(r'^$', login_required(PlayerView.as_view()), name='player'),
    url(r'^live/$', views.live),
    url(r'^live/tweet/$', views.post_tweet),
    url(r'^live/out/$', views.out),
    url(r'^mpd_action/(?P<action>\w+)$', views.mpd_action),
    url(r'^mpd_action_play_song/(?P<song_pos>\d+)$', views.mpd_play_song),
    url(r'^mpd_status/$', views.mpd_status),
    url(r'^update_list/$', plview.update_playlist),
    url(r'^reset_list/$', plview.reset_playlist),
    #url(r'^player/get_cover/(?P<episode_id>)$', views.get_cover)),
    url(r'^mpd_rewfor/(?P<percent>\d+)$', views.mpd_rewfor),
'''