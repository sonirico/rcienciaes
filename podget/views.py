#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import urllib2
from urlgrabber.grabber import URLGrabber
import feedparser
import dateutil.parser
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mpc.models import MPDC
import sys
from datetime import datetime
import time
from django.db import IntegrityError

reload(sys)
sys.setdefaultencoding("utf-8")

from playlist.models import Podcast, Episode
from playlist.views import update_playlist

if not os.path.exists('logs'):
    os.makedirs('logs')


class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"

logger = logging.getLogger(__name__)


class DownloadManager():
    def __init__(self):
        self.c = 0
        self.busy = False
        self.episodio = {} # Variable que contendra temporalmente los datos de cada episodio
        self.LOCAL_PATH = u'audios/'
        # La carpeta debe estar creada
        if not os.path.exists(self.LOCAL_PATH):
            os.makedirs(self.LOCAL_PATH)
        # Download Manager Logger
        global logger

    def is_busy(self):
        return self.busy

    def download_episode(self):
        relative_path = self.episodio['_local_path'] + self.episodio['_filename']
        # Comprobamos que un archivo tocallo no moleste. Formato audios/loquesea.mp3
        if not os.path.isfile(relative_path):
            logger.info('Descarga comenzada')
            logger.info('Descargando %s from %s' % (relative_path, self.episodio['url']))
            g = URLGrabber() # Instanciamos el asistente de descarga
            try:
                self.busy = True
                g.urlgrab(self.episodio['url'], filename=relative_path, reget="simple")
                logger.info('Descarga finalizada')
            except:
                self.busy = False
                # Cuando da error, hay veces que el fichero es creado pero vacío (0 bytes)
                # Por lo tanto debemos borrarlo manualmente.
                if os.path.isfile(relative_path):
                    os.remove(relative_path)
                logger.info('Unable to download current audio %s Skipping' % self.episodio['_filename'])
                return
            audio = None
            self.episodio['duration'] = 0
            try:
                if self.episodio['type'] == "audio/mpeg":
                    audio = MP3(relative_path)
                    self.episodio['duration'] = audio.info.length
                elif self.episodio['type'] == "audio/mp4":
                    audio = MP4(relative_path)
                    self.episodio['duration'] = audio.info.length
                # ¿Demasiado largo?
                logger.info('Duration: %s' % self.episodio['duration'])
                if self.episodio['duration'] >= (3600 * 3):
                    # Lo debemos borrar y pasar al siguiente
                    logger.info('This episode is too large, skipping.')
                    if os.path.isfile(relative_path):
                        os.remove(relative_path)
                    return
            except:
                logger.info('Unable to download current audio %s Skipping' % self.episodio['_filename'])
                return
            self.episodio['times_played'] = 0
            self.episodio['_date_downloaded'] = datetime.now()
            #insertamos el nuevo episodio en la bbdd
            new_episode = Episode(
                times_played=self.episodio['times_played'],
                duration=self.episodio['duration'],
                podcast=self.episodio['current_podcast'],
                url=self.episodio['url'],
                titulo=self.episodio['titulo'],
                _local_path=self.episodio['_local_path'],
                _filename=self.episodio['_filename'],
                _date_published=self.episodio['_date_published'],
                _date_downloaded=self.episodio['_date_downloaded']
            )
            try:
	            # Guardamos el episodio en la BBDD
    	        new_episode.save()
            except IntegrityError, e:
				# Lo debemos borrar y pasar al siguiente
                logger.info('Unable to save current episode by integrity error: %s' % e )
                if os.path.isfile(relative_path):
                    os.remove(relative_path)
                    return
            # Le indicamos a su podcast que será el episodio activo
            new_episode.set_active()
            # Finalmente, borramos los audios viejos del podcast del episodio recien descargado. Se consideran viejos,
            # aquellos episodios que no sean el episodio activo del podcast (Podcast.active_episode)
            # IMPORTANTE: Reinstanciamos el objeto con los datos del episodio activo actualizados
            related_podcast = Podcast.objects.get(pk=self.episodio['current_podcast'].id)
            related_podcast.remove_old_files()
            # Creamos la caratula
            new_episode.create_cover()
            #Y refrescamos la lista de reproduccion
            update_playlist()
            # Nota: en las 2 ultimas llamadas se invoca a la funcion save(), ergo aqui sobra.
            logger.info('Downloaded and data-recorded')
            #except:
            #    logging.info('Hubo un error al intentar descargar %s. Override',self.episodio['url'])

    def rss_from_database(self, from_=0, to=0):
        all_podcasts = Podcast.objects.filter(activo=True)
        if from_ == 0 and to == 0:
            from_ = 0
            to = all_podcasts.count() - 1
            # Si "to" < 0, no habia podcast en la BD
            if to < 0:
                logger.info('There is no podcasts in database')
                return
        self.busy = True
        for podcast in all_podcasts.order_by("nombre")[from_:to]:
            logger.info(podcast.nombre)
            self.episodio['current_podcast'] = podcast
            url_rss = podcast.rssfeed
            nombre = podcast.nombre
            logger.info('Extrayendo RSS de %s url: %s ' % (nombre, url_rss))
            item = self.search_episode(url_rss)
            if item is not None:
                #El episodio ya esta descargado anteriormente?
                downloaded_episodes = Episode.objects.filter(
                    _date_published=item['_date_published'],
                    podcast__nombre=nombre
                )
                if not downloaded_episodes.exists():
                    #construir un nombre de archivo único
                    extension = "." + str(item['audio_url']).split(".")[-1]
                    audio_name = nombre.replace(" ", "_")
                    audio_name = unicode(audio_name + "_" + time.strftime('%Y_%m_%d-%H_%M_%S'))
                    filename = audio_name + extension
                    self.episodio['extension'] = extension
                    self.episodio['podcast_id'] = Podcast.objects.get(nombre=nombre)
                    self.episodio['url'] = str(item['audio_url'])
                    self.episodio['titulo'] = str(item['title'])
                    self.episodio['_local_path'] = self.LOCAL_PATH
                    self.episodio['_filename'] = filename
                    self.episodio['_date_published'] = item['_date_published']
                    # Hay que comprobar que el audio que se descargaría no pertenece al mismo podcast del episodio que suena
                    if self.episodio['current_podcast'] != self.__what_podcast_is_playing():# and not os.path.isfile(filename):
                        logger.info('Filename: %s' % filename)
                        self.download_episode()
                    else:
                        logger.info('Skipping the download. Episode from same podcast already in the air: %s' % filename)
                else:
                    logger.info('Same episode already downloaded. Skipping')
        self.busy = False

    def search_episode(self, rss_url):
        try:
            rss = feedparser.parse(rss_url)
            rss = feedparser.parse(rss.href)# con esta linea tenemos en cuenta posibles redirecciones
        except:
            logger.info('Unable to parse this rss: %s' % rss_url)
            return None
        item = {}
        logger.info('Parsing rss data ... ')
        if len(rss.entries) > 0:
            # Hay que usar un bucle hasta encontrar una entrada con "enclosures", es decir, un audio.
            for last_entry in rss.entries:
                if hasattr(last_entry, 'enclosures') and len(last_entry.enclosures) > 0:
                    # Puede que haya varias "enclosures". Debemos encontrar la que tenga el atributo "type"
                    found = False
                    for last_enclosure in last_entry.enclosures:
                        if hasattr(last_enclosure, 'type'):
                            item['title'] = last_entry['title']
                            item['_date_published'] = self.datetime_with_format(last_entry)
                            item['audio_url'] = last_enclosure['href']
                            item['type'] = last_enclosure['type']
                            if item['type'] == "audio/x-m4a":
                                self.episodio['type'] = "audio/mp4"
                            else:
                                try:
                                    # miramos la cabecera del archivo online, dado que en el rss no siempre especifican el tipo
                                    request = HeadRequest(item['audio_url'])
                                    response = urllib2.urlopen(request)
                                    response_headers = response.info()
                                    self.episodio['type'] = response_headers['content-type']
                                except:
                                    logger.info('Error al intentar extraer el audio type. Asumimos mp3')
                                    self.episodio['type'] = "audio/mpeg"
                            found = True
                            break
                    if found:
                        logger.info('Enclosure with "type" found. Returning item.')
                        return item
                    else:
                        logger.info('No enclosure with "type" found. Next entry.')
                else:
                    logger.info('RSS entry has no enclosures')
        else:
            logger.info('RSS has no entries')
        if len(item) <= 0:
            logger.info('Unable to find some data. Returning None.')
            return None
        else:
            return item

    # Retorna el podcast del audio que está sonando
    def __what_podcast_is_playing(self):
        c = MPDC()
        c.connect()
        try:
            # audiofile = c.client.playlistid(c.client.status()['songid'])[0]['file']
            audio_filename = c.client.currentsong()['file']
            current_episode = Episode.objects.filter(_filename=audio_filename)[0]
            return current_episode.podcast
        except:
            pass
        finally:
            c.client.close()
            return None

    def datetime_with_format(self, entry):
        try:
            published = entry.published_parsed
            published = str(published[0])+"-"+str(published[1])+"-"+str(published[2])+\
                      " " + str(published[3])+":"+str(published[4])+":"+str(published[5])+"+0000"
            return dateutil.parser.parse(published)
        except:
            return None
