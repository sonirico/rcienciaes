# -*- coding: utf-8 -*-
import os
import json
import logging

from django.shortcuts import Http404
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from mpc.models import MPDC
from playlist.models import Episode, Podcast
from live.models import LiveEntry
from player.views import podcaster_in_the_air
from podcastmanager.settings import AUDIOS_URL, DEFAULT_COVER_IMAGE

# Create your views here.
logger = logging.getLogger(__name__)

def index(request):
    return HttpResponse('ok')


def live(request):
    data = {}
    if bool(podcaster_in_the_air()):
        live_entry = LiveEntry.objects.latest('start_date')
        data['live'] = 'on'
        data['artist'] = live_entry.artist
        data['event_title'] = live_entry.event_title
        data['start_date'] = live_entry.start_date.strftime("%Y-%m-%d %H:%M:%S")
        data['cover_path'] = live_entry.get_image_file()
    else:
        data['live'] = 'off'
    return HttpResponse(json.dumps(data))


def current(request):
    mpdc = MPDC()
    mpdc.connect()
    current_song = mpdc.client.currentsong()
    mpdc.client.close()
    if current_song:
        audio = get_audio_from_file(current_song.get('file'))
        if not audio:
            raise Http404
        current_song['cover'] = audio.get_cover()
        response = json.dumps(current_song)
        return HttpResponse(response, content_type='application/json')
    else:
        raise Http404


def status(request):
    mpdc = MPDC()
    mpdc.connect()
    response = json.dumps(mpdc.client.status())
    mpdc.client.close()
    return HttpResponse(response, content_type='application/json')


def playlistinfo(request):
    mpdc = MPDC()
    mpdc.connect()
    current_status = mpdc.client.status()
    mpd_playlist = mpdc.client.playlistinfo()
    mpdc.client.close()
    if mpd_playlist:  # Empty == False
        new_list = []
        for entry in mpd_playlist:
            # Obtenemos el link de la cover
            audio = get_audio_from_file(entry['file'])
            cover_url = audio.get_cover()
            entry['cover'] = str(cover_url)
            new_list.append(entry)
        return HttpResponse(json.dumps(new_list))
    else:
        raise Http404


def get_song_by_id(request, song_id):
    mpdc = MPDC()
    mpdc.connect()
    found = False
    song = None
    for entry in mpdc.client.playlistinfo():
        if entry['id'] == song_id:
            found = True
            song = entry
            break
    if found:
        audio = get_audio_from_file(song['file'])
        if not audio:
            raise Http404
        song['cover'] = audio.get_cover()
        response = json.dumps(song)
    else:
        response = 'Audio whose id = %s does not exist ' % song_id
    mpdc.client.close()
    return HttpResponse(response)


def get_song_by_pos(request, song_pos):
    mpdc = MPDC()
    mpdc.connect()
    found = False
    song = None
    for entry in mpdc.client.playlistinfo():
        if entry['pos'] == song_pos:
            found = True
            song = entry
            break
    if found:
        audio = get_audio_from_file(song['file'])
        if not audio:
            raise Http404
        song['cover'] = audio.get_cover()
        response = json.dumps(song)
    else:
        response = 'Audio whose id = %s does not exist ' % song_pos
    mpdc.client.close()
    return HttpResponse(response)


def get_audio_from_file(filename=None):
    if filename is not None:
        try:
            audio = Audio.objects.get(filename=os.path.join(AUDIOS_URL, filename))
            return audio
        except ObjectDoesNotExist, e:
            logger.exception(e.message)
            return False
    return False


from statistics.models import IceCastRetriever


def stats(request):
    try:
        retriever = IceCastRetriever()
        stats = retriever.raw_stats()
        del retriever
        return HttpResponse(json.dumps(stats), content_type='application/json')
    except Exception, e:
        raise Http404

# Sobre el podcast del episodio que está sonando, devuelve:
# Nombre del podcast, nombre del episodio , imagen del episodio, ...


def podcast(request):
    try:
        mpdc = MPDC()
        mpdc.connect()
        current_file = mpdc.client.currentsong().get('file')
        audio = get_audio_from_file(current_file)
        if not audio:
            raise Http404
        #current_podcast = current_episode.podcast
        data = {}
        data_type = audio.get_type()
        data['type'] = data_type
        if data_type == 'episode':
            data['podcast_name'] = audio.podcast.name
            data['podcast_description'] = audio.podcast.description
            data['podcast_web'] = audio.podcast.website
        data['audio_cover'] = audio.get_cover()
        data['audio_title'] = audio.title
        return HttpResponse(json.dumps(data), content_type='application/json')
    except:
        raise Http404


# Información sobre el siguiente podcast que sonara
# Nombre de episodio y podcast e imagen
def next_podcast(request):
    try:
        mpdc = MPDC()
        mpdc.connect()
        next_song_pos = mpdc.client.status().get('nextsong')
        next_file = mpdc.client.playlistinfo()[int(next_song_pos)].get('file')
        next_episode = Episode.objects.filter(_filename=next_file)[0]
        nextpodcast = next_episode.podcast
        data = {}
        data['podcast_name'] = nextpodcast.nombre
        data['podcast_image'] = next_episode.get_image_filename()
        data['episode_title'] = next_episode.titulo
        return HttpResponse(json.dumps(data))
    except:
        return Http404()

from django.contrib.contenttypes.models import ContentType
from playlist.models import PlayListManager

def playlist(request):
    pm = PlayListManager()
    data = {}
    rows = []
    files = pm.get_files_in_playlist(folder=AUDIOS_URL)
    audios = Audio.objects.filter(filename__in=files)
    pos = 0
    for audio in audios:
        # Episode or audio
        data_pod = {}
        audio_type = audio.get_type()
        if audio_type == 'episode':
            data_pod['podcast_name'] = audio.podcast.name
        elif audio_type == 'promotion':
            data_pod['expiration'] = str(audio.expiration)
            data_pod['uploaded'] = str(audio.uploaded)
            data_pod['tweet'] = audio.tweet
        # Common attributes
        data_pod['pos'] = pos
        #data_pod['podcast_image'] = episode.get_image_filename()
        data_pod['audio_title'] = audio.title
        data_pod['audio_type'] = audio_type
        rows.append(data_pod)
        pos += 1
    data['rows'] = rows
    data['total'] = audios.count()
    data['current'] = 1
    data['rowCount'] = 4
    return HttpResponse(json.dumps(data), content_type='application/json')

# Playlist del día: información para visualizar la playlist del podcast del día (nombre, episodio, imagen)


def podcast_by_id(request, podcast_id):
    try:
        pod = Podcast.objects.get(pk=podcast_id)
        data = {}
        data['id'] = pod.id
        data['name'] = pod.nombre
        data['feed'] = pod.rssfeed
        data['web'] = pod.web
        data['categoria'] = pod.categoria.nombre
        data['active'] = pod.activo
        data['image'] = DEFAULT_COVER_IMAGE
        try:
            data['active_episode_id'] = pod.active_episode.id
            data['image'] = pod.active_episode.get_image_filename()
            data_ep = {}
            i = 0
            for e in Episode.objects.filter(podcast=pod):
                data_ep[i] = dict(episode_by_id(e))
                i += 1
            data['episodes'] = data_ep
        except:
            pass
        data['description'] = pod.descripcion
        print data
        return HttpResponse(json.dumps(data))
    except:
        return Http404()


# Información completa de un podcast: dado un podcast (del que tenga su id), obtener toda
# la información posible del mismo, nombre, imagen, episodios sonando en la radio, etc.


def episode_by_id(e):
    data = {}
    data['id'] = e.id
    data['titulo'] = e.titulo
    data['url'] = e.url
    data['date_published'] = str(e._date_published)
    data['date_downloaded'] = str(e._date_downloaded)
    return data



from django.views.generic import ListView
from playlist.models import Audio
from django.http import JsonResponse


class AudioListView(ListView):
    title = 'Audio List'
    queryset = Audio.objects.order_by('-title')

    def get_context_data(self, **kwargs):
        context = super(AudioListView, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context
