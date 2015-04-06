#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf.urls import patterns

from player import views
from playlist import views as plview
from django.contrib import admin


#funcion que permite ver el player desde el panel de admin
def get_admin_urls(urls):
    def get_urls():
        my_urls = patterns('',
            (r'^player/$', admin.site.admin_view(views.index)),
            (r'^player/live/$', admin.site.admin_view(views.live)),
            (r'^player/live/tweet/$', admin.site.admin_view(views.post_tweet)),
            (r'^player/live/out/$', admin.site.admin_view(views.out)),
            (r'^player/mpd_action/(?P<action>\w+)$', admin.site.admin_view(views.mpd_action)),
            (r'^player/mpd_action_playsong/(?P<song_pos>\d+)$', views.mpd_play_song),
            (r'^player/mpd_status/$', admin.site.admin_view(views.mpd_status)),
            (r'^player/update_list/$', admin.site.admin_view(plview.update_playlist)),
            (r'^player/reset_list/$', admin.site.admin_view(plview.reset_playlist)),
            #(r'^player/get_cover/(?P<episode_id>)$', admin.site.admin_view(views.get_cover)),
            (r'^player/refresh_covers/$', admin.site.admin_view(views.refresh_covers)),
            (r'^player/mpd_rewfor/(?P<percent>\d+)$', admin.site.admin_view(views.mpd_rewfor)),
        )
        return my_urls + urls
    return get_urls

admin_urls = get_admin_urls(admin.site.get_urls())
admin.site.get_urls = admin_urls

