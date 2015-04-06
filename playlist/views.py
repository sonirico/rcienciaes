#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
import opml
import logging
from django.db import IntegrityError
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseRedirect
from playlist.models import *
from podcastmanager.settings import TWITTER_OAUTH
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

from twitter import *

if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger(__name__)


# Crea un usuario por cada podcast en funcion del nombre de éste y los añade al grupo "podcasters"
# Si exististieran previamente usuarios en este grupo, los borra
def create_podcaster(podcast_nombre=''):
    logger.info('Adding new podcaster ...')
    try:
        pod_group = Group.objects.get(name='podcasters')
        username = unicode(podcast_nombre)
        redone_username = remove_accents(username)
        if len(redone_username) > 4:
            username = redone_username[:15]
        try:
            new_user = User(username=username, is_staff=True, is_active=True)
            new_user.set_password('cambiaesto')
            new_user.save()
            pod_group.user_set.add(new_user)
            logger.info('Added. %s.' % username)
        except IntegrityError:
            logger.info('User "%s" already stored. Skipping.' % username)
    except ObjectDoesNotExist:
        logger.info('Unable to create new podcaster. Podcasters group does not exist.')


import unicodedata
import string


# Procesa el nombre del podcast y lo convierte en nombre de usuario
def remove_accents(data):
    return ''.join(x for x in unicodedata.normalize('NFKD', data) if x in string.ascii_letters).lower()


def import_from_opml(opml_file="podcasts.opml"):
    global logger
    if os.path.isfile(opml_file):
        outline = opml.parse(opml_file)
        default_category = Categoria.objects.get(pk='2')
        logger.info('Beginning podcast import operation.')
        for podcast in outline:# Each "outline" tag represents one podcast
            podcast_name = podcast.text # Podcast name
            rss_url = podcast.xmlUrl    # Podcast rss
            web_url = podcast.htmlUrl   # Podcast web
            logger.info('Importing %s ...' % podcast_name)
            # Si vamos a importar un nuevo fichero opml, puede que se repitan podcast. Considerando que este nuevo
            # opml será más reciente, actualizamos tanto la web como el nombre del podcast.
            # La premisa principal, es que un RSS nunca cambia de url, ya que es el campo de comparación. En otras palabras
            # se toma como clave primaria la url del rss feed (Algo que no me gusta).
            old_podcasts = Podcast.objects.filter(rssfeed=rss_url)
            if old_podcasts.count() == 1:
                # Podcast existente. Actualizamos datos.
                logger.info('Podcast already stored. Updating it ...')
                old_podcast = old_podcasts[0]
                old_podcast.nombre = podcast.text
                old_podcast.web = podcast.htmlUrl
                old_podcast.save()
            elif old_podcasts.count() > 1: # Mas de un podcast con el mismo feed. Nunca debería entrar aquí.
                logger.info('Too many podcast for one feed.')
            else:
                # No hay podcasts coincidentes. Lo creamos.
                logger.info('Creating new podcast ...')
                new_podcast = Podcast(
                    nombre=podcast_name,
                    rssfeed=rss_url,
                    web=web_url,
                    categoria=default_category
                )
                new_podcast.save()
            create_podcaster(podcast_name)
            logger.info('Done.')
        logger.info('Importing podcast tasks : Done')
        return HttpResponse('Done all imports.')
    else:
        return HttpResponse('Unable to find the submitted opml file: ' + opml_file)
# End import_from_opml

#Crea una lista de cero. Borra las canciones que hubiera antes.
#En otras palabras, se reinicia la reproduccion
from playlist.models import PlayListManager


def reset_playlist(request=None):
    global logger
    logger.info('Reseting playlist.')
    # Objeto con el que manejaremos la playlist
    plm = PlayListManager()
    plm.reset_playlist()
    # Seleccionamos los podcasts activos con un audio activo
    all_active_podcasts = Podcast.objects\
        .filter(activo=True)\
        .exclude(active_episode=0)\
        .order_by('nombre')
    if not all_active_podcasts.exists():
        logger.info('No active podcasts. Aborted')
        return HttpResponseRedirect('/admin/player/')
    for podcast in all_active_podcasts:
        # ¿Que pasa si el podcast no tiene ningun audio anterior? En teoria no debería suceder porque
        # el .exclude() criba los que no tengan audio. En este punto debería tener al menos 1.
        try:
            episode = podcast.active_episode #Episode.objects.get(pk=podcast.active_episode.id)
            if episode is not None:
                # ¿El episodio ha llegado al limite de reproducciones ?
                if episode.times_played < podcast.get_max_repro():
                    # Entonces lo incluimos en la lista
                    plm.add_song(episode.get_file_name())
                    logger.info('Added to playlist: %s' % episode.get_file_name())
        except Exception, e:
            pass

    logger.info('Reset playlist: Done.')
    plm.play()
    plm.close()
    return HttpResponseRedirect('/admin/player/')
# End reset_playlist


# refrescamos la lista sustituyendo el audio viejo por el nuevo de un episodio
# Normalmente esta operacion se suele realizar tras haber descargado un episodio
# sirve para intercambiar un episodio viejo por uno nuevo de un podcast. Esto solo
# se puede llevar a cabo, si el audio que suena no pertenece al mismo podcast del recien descargado.
def update_playlist(request=None):
    global logger
    logger.info('Updating playlist.')
    plm = PlayListManager()
    # Si de entrada, no hay nada en la lista ...
    if len(plm.get_playlist_info()) < 1:
        reset_playlist()
        return
    elif plm.status()['state'] != 'play':
        plm.play()
    # Seleccionamos los podcasts activos con un audio activo
    all_active_podcasts = Podcast.objects\
        .filter(activo=True)\
        .exclude(active_episode=0)\
        .order_by('nombre')
    if not all_active_podcasts.exists():
        logger.info('No active podcasts. Update aborted. ')
        return HttpResponseRedirect('/admin/player/')
    current_song = plm.get_current_song() # El audio que estaba sonando antes
    current_time = plm.get_current_song_time() # El segundo donde current_song estaba
    old_episode = Episode.objects.filter(_filename=current_song['file'])[0]
    # Resetamos la playlist
    plm.reset_playlist()
    for podcast in all_active_podcasts:
        try:
            episode = podcast.active_episode
            if episode is not None:
                if episode.times_played < podcast.get_max_repro():
                    # Entonces lo incluimos en la lista
                    plm.add_song(episode.get_file_name())
                    logger.info('Added to playlist: %s' % episode.get_file_name())
        except:
            pass
    # Seleccionamos la nueva posicion en la playlist
    new_playlist = plm.get_playlist_info()
    # Solo seleccionamos la cancion que sonaba cuando la playlist anterior no estaba vacia
    # ¿Que pasaria si el audio ya no está? Vuelve desde 0
    audio_found = False
    for audio in new_playlist:
        if audio['file'] == current_song['file']:
            plm.move(audio['id'])
            plm.seek(audio['id'], current_time)
            audio_found = True
            break
    if not audio_found:
        logger.info('Previous sounding audio not found. Seeking the appropriate newer')
        #  Debemos recorrer la vieja playlist y encontrar el audio que se estaba reproduciendo. Despues, se cogera
        #  la sigguiente, siempre y cuando vaya a ser reproducida
        search_next = False
        found = False
        for podcast in all_active_podcasts:
            try:
                episode = podcast.active_episode
                if episode is None:
                    continue
            except:
                continue
            if podcast == old_episode.podcast and not search_next:
                search_next = True
                logger.info('Episode from old episode podcast found, searching the next')
                continue
            if search_next:
                for audio in new_playlist:
                    if audio['file'] == episode.get_file_name():
                        logger.info('Move cursor to %s ' % audio['file'])
                        plm.move(audio['id'])
                        found = True
                        break
            if found:
                break
        if not found:
            logger.info('No parallel audio has been found. ')
    plm.play()
    plm.close()
    logger.info('PLaylist updated successfully ')
    return HttpResponseRedirect('/admin/player/')


def tweet_new_audio(request):
    bird = Twitter(auth=OAuth(
            TWITTER_OAUTH['ACCESS_TOKEN'],
            TWITTER_OAUTH['ACCESS_TOKEN_SECRET'],
            TWITTER_OAUTH['CONSUMER_KEY'],
            TWITTER_OAUTH['CONSUMER_KEY_SECRET']
        )
    )
    # Si había una entrada en el historial de reproducciones, marcamos su fin.
    history = PlayHistory.objects.all().order_by('-ini')
    if history.count() > 0:
        ph = history[0]
        ph.stop()
    c = MPDC()
    c.connect()
    # Seleccionamos el episodio que está sonando
    current_file = c.client.currentsong().get('file')
    c.client.close()
    episode = Episode.objects.get(_filename=current_file)
    episode.play()
    tweet = '#RadioPodcastellano #' + str(episode.times_played) + ': En el aire: "' + str(episode.titulo) + \
            '" de "' + str(episode.podcast.nombre) + '"'
    c.client.close()
    #bird.statuses.update(status=tweet[:140])
    logger.info('Tweet sent: "%s"' % tweet)
    return HttpResponse('Tweet sent : ' + tweet)


def tweet(text):
    try:
        bird = Twitter(auth=OAuth(
                TWITTER_OAUTH['ACCESS_TOKEN'],
                TWITTER_OAUTH['ACCESS_TOKEN_SECRET'],
                TWITTER_OAUTH['CONSUMER_KEY'],
                TWITTER_OAUTH['CONSUMER_KEY_SECRET']
            )
        )
        bird.statuses.update(status=text[:140])
        return True
    except Exception, e:
        print e
        return False
