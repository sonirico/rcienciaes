#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from datetime import datetime,timedelta

from django.utils import timezone
from django.db import models
from django.conf.urls import patterns
from mpc.models import MPDC

from playlist.models import Sound, PlayHistory, Episode, TaskScheduler


class Player():
    buttons = []

    def __init__(self):
        self.buttons.extend([Play(), Stop(), Pause(), Next(), Previous()])

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


class Button:
    __metaclass__ = ABCMeta

    @abstractmethod
    def action(self):
        pass

# TODO: Revisar algoritmia en esta funcion. Problemática en un futuro.
class Play(Button):
    action_name = "play"

    def action(self, client):
        if client.status().get('state', None) == 'pause':
            client.play()
        else:
            if client.status().get('state', None) == 'stop':
                current_file = client.currentsong().get('file')
                # Implica que la reproduccion ha sido detenida con ~# mpc stop y que desde el reproductor
                # mediante la accion play, no se emprenderá la acción play debido a que no hay un archivo
                # sonando o cargado (campo songid).
            client.play()


class Pause(Button):
    action_name = 'pause'

    def action (self, client):
        if client.status().get('state', None) == 'play':
            client.pause()
        else:
            if client.status().get('state', None) == 'pause':
                currentfile = client.currentsong().get('file')
            client.play()


class Stop (Button):
    action_name = "stop"

    def action (self,client):
        if client.status().get('state',None) != 'stop':
            #TODO prueba de cordura con currentsong
            if len(PlayHistory.objects.all().order_by('-ini'))>=1:
                ph=PlayHistory.objects.all().order_by('-ini')[0]
                ph.stop()
            #eliminamos las tasks stop_sound_task
            #q=TaskScheduler.objects.filter(periodic_task__task="player.tasks.stop_sound_task")
            #for t in q:
                #t.terminate()
            client.stop()


class Next (Button):
    action_name = "next"

    def action(self,client):
        client.next()


class Previous(Button):
    action_name = "previous"

    def action (self,client):
        client.previous()


class PlayerWrapper(models.Model):
    def __unicode__(self):
        return self.title

    class Meta(object):
        def __init__(self):
            verbose_name = "Reproductor"






