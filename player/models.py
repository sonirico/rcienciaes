#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from django.db import models
from mpc.models import MPDC
from playlist.models import PlaylistHistory as PlayHistory, PlayListManager
from django.core.exceptions import ObjectDoesNotExist
from podcastmanager.settings import AUDIOS_URL
import logging

logger = logging.getLogger(__name__)


class Player():
    buttons = []

    def __init__(self):
        self.buttons.extend([
            Play(),
            Stop(),
            Pause(),
            Next(),
            Previous(),
            #Refresh()
        ])

    def get_status(self):
        c = MPDC()
        c.connect()
        output = c.client.status()
        c.client.close()
        return output


    def get_playlist_info(self):
        c = MPDC()
        c.connect()
        song_info_list = []
        lista = c.client.playlistinfo()
        # TODO: A veces, el playlistinfo no puede almacenar datos como el titulo del audio, o el artista.
        # Esto supone, que en la playlist del reproductor no saldrán datos que si deberían
        # Cuando esto sucede, hay que sacar los datos de la BD
        for l in lista:
            song_info_list.append(l)
        c.client.close()
        return song_info_list


class Button():
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def action(self):
        pass


class LastRegisteredAudioNotInPlaylist(Exception):
    def __init__(self):
        logger.exception(
            u'The last registered audio is not in the current playlist. Playlist must have been refreshed manually'
        )


class ShouldHaveBeenPlaylistHistoryException(Exception):
    def __init__(self):
        logger.exception(u'There have been audios on the air which might have been not registered in history.')


class Play(Button):
    def __init__(self):
        self.action_name = "play"

    def action(self, client):
        state = client.status().get('state', None)
        if state == 'pause':
            client.play()
        elif state == 'stop':
            '''
                Al parar la playlist, la reproducción regresa a la posición 0. Cogiendo la última entrada del
                historial se replayea el último que sonaba
            '''
            try:
                latest_audio = PlayHistory.objects.latest('started')
                pm = PlayListManager()
                pos = 0
                found = False
                for file_name in pm.get_files_in_playlist():
                    if file_name == latest_audio.audio.get_filename():
                        client.play(pos)
                        found = True
                        break
                    pos += 1
                if not found:
                    raise LastRegisteredAudioNotInPlaylist
            except ObjectDoesNotExist:
                raise ShouldHaveBeenPlaylistHistoryException


class Pause(Button):
    def __init__(self):
        self.action_name = 'pause'

    def action(self, client):
        if client.status().get('state', None) == 'play':
            client.pause()
        '''
        if client.status().get('state', None) == 'play':
            client.pause()
        else:
            if client.status().get('state', None) == 'pause':
                currentfile = client.currentsong().get('file')
            client.play()
        '''

'''
from playlist.views import update_playlist


class Refresh(Button):
    def __init__(self):
        self.action_name = 'refresh'

    def action(self):
        update_playlist(None)
'''

class Stop(Button):
    def __init__(self):
        self.action_name = "stop"

    def action(self,client):
        if client.status().get('state', None) != 'stop':
            '''
            #TODO prueba de cordura con currentsong
            if len(PlayHistory.objects.all().order_by('-ini')) >= 1:
                ph = PlayHistory.objects.all().order_by('-ini')[0]
                ph.stop()
            #eliminamos las tasks stop_sound_task
            #q=TaskScheduler.objects.filter(periodic_task__task="player.tasks.stop_sound_task")
            #for t in q:
                #t.terminate()
            '''
            client.stop()


class Next(Button):
    def __init__(self):
        self.action_name = "next"

    def action(self,client):
        client.next()


class Previous(Button):
    def __init__(self):
        self.action_name = "previous"

    def action(self,client):
        client.previous()


class PlayerWrapper(models.Model):
    def __unicode__(self):
        return self.title

    class Meta():
        verbose_name = u'Reproductor'
        abstract = True






