#!/usr/bin/env python
# -*- coding: utf-8 -*-

from djcelery import celery
from podget.views import DownloadManager
from playlist.views import update_playlist


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

