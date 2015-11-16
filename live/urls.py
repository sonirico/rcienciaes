from django.conf.urls import url
from django.contrib.auth import views as auth_views
from .views import *


urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    #url(r'^/(?P<)$', IndexView.as_view(), name='index'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^login/wait/$', WaitView.as_view(), name='wait'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^password_change/$', auth_views.password_change, name='password_change'),
    url(r'^password_change/done/$', auth_views.password_change_done, name='password_change_done'),

    url(r'^create/$', EventCreateView.as_view(), name='event-create'),
    url(r'^on/$', LiveModeOn.as_view(), name='on'),
    url(r'^off/$', LiveModeOff.as_view(), name='off'),

    url(r'^on/tweet/$', TweetView.as_view(), name='tweet'),
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