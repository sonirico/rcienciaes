#!usr/bin/env python
#-*- coding: utf-8 -*-

import httplib2
from mpd import MPDClient
import time
from podcastmanager.settings import DOMAIN, PORT

def scan_state(c, status_anterior):
    status_actual = c.status()
    if status_actual['state'] == 'play' and status_anterior['state'] == 'stop':
#        enviar()
        pass
    if status_actual['state'] != status_anterior['state']:
        print "nuevo estado: ", str(status_actual['state'])
        return status_actual['state']

def scan_song(c, status_anterior):
    status_actual = c.status()
    #if hasattr (status_actual,'songid'):
    if status_actual['song'] != status_anterior['song']:
        print "nuevo audio: "
        print c.currentsong()['id']
        print c.currentsong()['file']
        try:
            print c.currentsong()['artist']
            print c.currentsong()['title']
        except:
            print "The current episode has no associated artist and title according to MPD"
        enviar()
        return status_actual
    return status_anterior

def enviar():
#    from playlist import views
#    views.tweet_new_audio()
#    tweet_new_audio()
    h = httplib2.Http(".cache")
    url = 'http://%s:%s/playlist/refresh/' % ( DOMAIN, PORT )
    #url = 'http://localhost:8000/playlist/refresh/'
    content = h.request(url, "GET")


c = MPDClient()
c.connect('localhost', 6600)

status_anterior = c.status()
status_actual = None

# Cada segundo comprobamos si el audio se ha cambiado
while True:
    if c.status()['state'] == 'play':
        #status_anterior['state'] = scan_state(c, status_anterior)
         status_anterior = scan_song(c, status_anterior)
         time.sleep(1)
