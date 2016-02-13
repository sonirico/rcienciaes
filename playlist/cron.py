#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import glob
import kronos
import logging

from podget.models import DownloadManager
from playlist.views import update_playlist
from live.views import is_anybody_online
from mpc.models import MPDC
from podcastmanager.settings import MEDIA_URL, AUDIOS_URL, TWITTER_ENABLED
from playlist.models import Episode, Promotion
from django.core.exceptions import ObjectDoesNotExist
from playlist.views import tweet
from playlist.models import PlaylistHistory, PlayListManager, Audio, Podcast
from django.utils import timezone

logger = logging.getLogger(__name__)

pm = PlayListManager()
dm = DownloadManager()


@kronos.register('0 4 * * *')
def download(from_=0, to=0):
    global dm
    if not dm.is_busy():
        dm.download(from_, to)


@kronos.register('* 0/6 * * *')
def update():
    update_playlist(None)


@kronos.register('* * * * *')
def check_streaming():
    if not is_anybody_online():
        pm = PlayListManager()
        if pm.status().get('state') != 'play':
            pm.play()
            logger.info('Playlist was either paused or stopped. Resuming.')
        pm.close()


@kronos.register('0 6 * * sun')
def clean_old_data():
    """
        Check weekly how many audios are on audios/ folder and compare them
        with the ones from active episodes. If they don't match, old files
        will be erased from file system.

        TODO: Do something with Episode/Promo inheritance
    """
    logger.info('Cleaning standalone files on disk...')
    for absolute_path in glob.glob(MEDIA_URL + '*'):
        file_name = os.path.basename(absolute_path)
        try:
            relative_path = os.path.join(AUDIOS_URL, file_name)
            audio = Audio.objects.get(filename=relative_path)
            if audio.get_type() == 'episode':
                try:
                    # If there are inactive audios on its being
                    for e in audio.podcast.episode_set.exclude(pk=audio.podcast.active_episode.pk):
                        if not e.is_active():
                            logger.info('Inactive audio found in podcast set. Erasing files.')
                            e.delete_files()
                except Exception, e:
                    logger.exception(e.message)
        except ObjectDoesNotExist, e:
            logger.info('A file with no audio registered in database')
            if os.path.isfile(relative_path):
                logger.info('Erasing: %s' % relative_path)
                os.remove(relative_path)
    logger.info('... Done.')


@kronos.register('* * * * *')
def check_new_audio():
    pm = PlayListManager()
    if pm:
        try:
            last_entry = PlaylistHistory.objects.latest('started')
            last_audio_file = last_entry.audio.get_filename()
            if last_audio_file is not False:
                current_song = pm.get_current_song().get('file')
                if last_audio_file != current_song:
                    # There is new audio
                    last_entry.stop()
                    # Set the next episode just in case the type of the current audio is "episode"
                    if last_entry.audio.get_type() == 'episode':
                        podcast = last_entry.audio.podcast
                        podcast.active_episode = podcast.get_next_episode()
                        podcast.save()
                    try:
                        current_audio = Audio.objects.get(filename=os.path.join(AUDIOS_URL, current_song))
                        current_audio.play()
                        if TWITTER_ENABLED:
                            tweet(current_audio)
                    except Exception, e:
                        pass
        except ObjectDoesNotExist, e:
            logger.info('Playlist history is empty. First record.')
            current_song = pm.get_current_song().get('file')
            if current_song:
                try:
                    audio = Audio.objects.get(filename=os.path.join(AUDIOS_URL, current_song))
                    audio.play()
                except ObjectDoesNotExist, e:
                    logger.error('There is a file in the playlist which no associated audio recorded')
    pm.close()



@kronos.register('0 0 1 * *')
def podcast_feels_old():
    for p in Podcast.objects.filter(active=True):
        try:
            episode = p.episode_set.latest('downloaded')
        except ObjectDoesNotExist, e:
            continue
        # Its last episode publication
        episode_publication = episode.published
        if episode_publication is None:
            episode_publication = p.active_episode.download
        days = (timezone.now() - episode_publication).days
        if days > p.category.days_to_inactive:
            logger.info('Marked as inactive: %s' % p.name)
            p.active = False
            p.save()

