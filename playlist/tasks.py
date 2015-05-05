#!/usr/bin/env python
# -*- coding: utf-8 -*-

from djcelery import celery
from podget.views import DownloadManager
from playlist.views import update_playlist
from player.views import podcaster_in_the_air
from mpc.models import MPDC, MPDCConnectionError

dm = DownloadManager()
# Both are invoked while the managers is not working


@celery.task
def download(from_=0, to=0):
    global dm
    if not dm.is_busy():
        dm.rss_from_database(from_, to)


@celery.task
def update():
    global dm
    if not dm.is_busy():
        update_playlist(None)


@celery.task
def check_streaming():
    global dm
    if not podcaster_in_the_air() and not dm.is_busy():
        c = MPDC()
        if c.connect():
            if c.client.status().get('state') != 'play':
                c.client.play()
            c.client.close()