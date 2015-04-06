# -*- coding: utf-8 -*-

from django.shortcuts import Http404
from django.http import HttpResponse
from mpc.models import MPDC
from playlist.models import Episode, Podcast, LiveEntry
from player.views import podcaster_in_the_air

import json

# Create your views here.

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
    response = 'Nothing sounding'
    current_status = mpdc.client.status()
    if current_status['state'] == 'play':
        current_song = mpdc.client.currentsong()
        cover_url = get_cover_from_file(current_song['file'])
        current_song['cover'] = cover_url
        response = json.dumps(current_song)
    mpdc.client.close()
    return HttpResponse(response)


def status(request):
    mpdc = MPDC()
    mpdc.connect()
    response = json.dumps(mpdc.client.status())
    mpdc.client.close()
    return HttpResponse(response)


def playlistinfo(request):
    mpdc = MPDC()
    mpdc.connect()
    current_status = mpdc.client.status()
    if current_status['state'] == 'play':
        playlist = mpdc.client.playlistinfo()
        new_list = []
        for entry in playlist:
            # Obtenemos el link de la cover
            cover_url = get_cover_from_file(entry['file'])
            entry['cover'] = str(cover_url)
            new_list.append(entry)
        mpdc.client.close()
        return HttpResponse(json.dumps(new_list))
    mpdc.client.close()
    return HttpResponse('Nothing sounding')


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
        song['cover'] = get_cover_from_file(song['file'])
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
        song['cover'] = get_cover_from_file(song['file'])
        response = json.dumps(song)
    else:
        response = 'Audio whose id = %s does not exist ' % song_pos
    mpdc.client.close()
    return HttpResponse(response)


def get_cover_from_file(filename=None):
    if filename is None: return
    episodes = Episode.objects.filter(_filename=filename)
    if episodes.exists():
        episode = episodes[0]
        cover = episode.get_image_filename()
        return cover

# Sobre el podcast del episodio que está sonando, devuelve:
# Nombre del podcast, nombre del episodio , imagen del episodio, ...
def podcast(request):
    try:
        mpdc = MPDC()
        mpdc.connect()
        current_file = mpdc.client.currentsong().get('file')
        current_episode = Episode.objects.filter(_filename=current_file)[0]
        current_podcast = current_episode.podcast
        data = {}
        data['podcast_name'] = current_podcast.nombre
        data['podcast_description'] = current_podcast.descripcion
        data['podcast_web'] = current_podcast.web
        data['podcast_image'] = current_episode.get_image_filename()
        data['episode_title'] = current_episode.titulo
        return HttpResponse(json.dumps(data))
        #return HttpResponse(serializers.serialize('json', current_episode), mimetype='application/json')
    except:
        return Http404()


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


def playlist(request):
    try:
        mpdc = MPDC()
        mpdc.connect()
        data = {}
        i = 0
        for entry in mpdc.client.playlistinfo():
            episode = Episode.objects.get(_filename=entry.get('file'))
            podcast = episode.podcast
            data_pod = {}
            data_pod['podcast_name'] = podcast.nombre
            data_pod['podcast_image'] = episode.get_image_filename()
            data_pod['episode_title'] = episode.titulo
            data[i] = data_pod
            i += 1
        return HttpResponse(json.dumps(data))
    except:
        return Http404()
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
        data['image'] = 'default.png'
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