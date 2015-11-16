#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime
import sys

from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required, user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from mpc.models import MPDC
from player.models import Player
from playlist.models import Episode, PlaylistHistory as PlayHistory
from forms import *
from live.models import Event
from playlist.views import tweet


reload(sys)
sys.setdefaultencoding("utf-8")


class CoverException(Exception):
    def __init__(self):
        pass


class EpisodeException(Exception):
    def __init__(self):
        pass


def get_playlist_data():
    return HttpResponse('hola')
    player = Player()
    playlist = player.get_playlist_info()
    episode_list = []
    all_episodes = Episode.objects.all()
    total_time = 0
    pos = 0
    for audio in playlist:
        total_time += int(audio['time'])
        for episode in all_episodes.filter(_filename=audio['file']):
            if episode.get_file_name() == audio['file']:
                setattr(episode, 'pos', pos)
                try:
                    ph = PlayHistory.objects.filter(object_id=episode.id).latest('ini')
                    setattr(episode, 'last_played', ph)
                except ObjectDoesNotExist:
                    setattr(episode, 'last_played', None)
                episode.duration = audio['time']
                episode_list.append(episode)
                break
        pos += 1
    data = {}
    data['episode_list'] = episode_list
    data['total_time'] = total_time
    return data


def render_admin(request):
    data = get_playlist_data()
    return render(request, 'index.html', {
        'title': 'Reproductor',
        #'episode_list': data['episode_list'],
        #'total_time': data['total_time'],
    })


def render_podcaster(request):
    # Comprobamos que no haya nadie en el aire
    if podcaster_in_the_air():
        return render(request, 'no_air.html', {})
    data = {}
    data['episode_list'] = None
    data['total_time'] = None
    if request.method == 'POST':
        form = LiveForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            live_entry = Event(
                user=request.user,
                event_title=cd['event_title'],
                artist=cd['artists'],
                start_date=datetime.now()
            )
            live_entry.save()
            live_entry.cover_file = live_entry.handle_cover(cd['image_file'])
            live_entry.save()
            # Creamos la variable global de sesión
            request.session['is_live'] = True
            # Pausamos la reproduccion
            pause()
            # Tuiteamos el contenido
            tweet(unicode(cd['content']))
            # Lo redirigimos a modo live
            return redirect('/admin/player/live/')
    else:
        data = get_playlist_data()
        form = LiveForm(initial={})
    return render(request, 'podcaster.html', {
        'form': form,
        'my_title': 'Live',
        'episode_list': data['episode_list'],
        'total_time': data['total_time'],
    })


def index(request):
    # Check whether there is someone already
    if request.session.get('is_live', False):
        return live(request)
    if request.user.is_authenticated():
        is_admin = request.user.groups.filter(name='administradores').exists()
        if is_admin:
            return render_admin(request)
        else:# Is podcaster
            return render_podcaster(request)
    else:
        raise Http404

@login_required
@staff_member_required
def mpd_action(request, action):
    c = MPDC()
    c.connect()
    player = Player()
    for button in player.buttons:
        if action == button.action_name:
            button.action(c.client)
            break
    else:
        raise Http404
    return HttpResponse()

@login_required
@staff_member_required
def mpd_rewfor(request, percent=-1):
    percent = int(percent)
    if percent < 0 or percent > 100:
        return HttpResponse('Nothing to do')
    c = MPDC()
    c.connect()
    current_pos = c.client.currentsong()['pos']
    total_time = int(c.client.currentsong()['time'])
    final_time = int(total_time * percent / 100)
    c.client.seek(current_pos, final_time)
    c.client.close()
    return HttpResponse('Done')

@login_required
@staff_member_required
def mpd_status(request):
    c = MPDC()
    c.connect()
    status = c.client.status()
    #status['image'] = Episode.objects.get(_filename=c.client.currentsong()['file'])._image_filename
    response = json.dumps(status)
    c.client.close()
    return HttpResponse(response, content_type='application/json')

@login_required
@staff_member_required
def mpd_play_song(request, song_pos):
    c = MPDC()
    c.connect()
    for entry in c.client.playlistinfo():
        if entry.get('pos') == song_pos:
            c.client.play(int(song_pos))
            break
    c.client.close()
    return HttpResponse()




def get_cover(request, episode_id):
    pass
    '''
    if request.is_ajax():
        print request.POST['filename']
        episode = Episode.objects.all().filter(filename__=filename)
        print episode
        if episode is None:
            raise Http404
        return HttpResponse(episode._image_filename, content_type='text')
    else:
        raise Http404
'''

@login_required
@staff_member_required
@user_passes_test(lambda u: u.groups.filter(name='podcasters').exists(), login_url='/admin/login/')
def live(request):
    if not request.session.get('is_live'):
        return redirect('/admin/login/')
    if request.method == 'POST':
        form = TweetForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            tweet_content = cd['content']
            if len(tweet_content) > 0:
                tweet(unicode(tweet_content))
                return HttpResponse('')
            # Enviar tuit
    form = TweetForm()
    return render(request, 'live.html', {
        'form': form,
        'my_title': 'Live'
    })


@login_required
@staff_member_required
def post_tweet(request):
    if request.is_ajax() and request.method == 'POST':
        form = TweetForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            tweet_content = cd['content']
            if len(tweet_content) > 0:
                tweet(unicode(tweet_content))
                return HttpResponse('')
    raise Http404


@login_required
@staff_member_required
def out(request):
    try:
        last_live_entry = Event.objects.latest('start_date')
        last_live_entry.end_date = datetime.now()
        last_live_entry.save()
        play()
        del request.session['is_live']
    except ObjectDoesNotExist:
        # Nunca se debería entrar aqui ...
        pass
    return redirect('/admin/logout/')


def pause():
    try:
        c = MPDC()
        c.connect()
        if c.client.status().get('state') == 'play':
            c.client.pause()
        c.client.close()
    except Exception, e:
        print e


def play():
    try:
        c = MPDC()
        c.connect()
        c.client.play()
        c.client.close()
    except Exception, e:
        print e


from django.views.generic import ListView
from playlist.models import PlayListManager
from playlist.models import Audio, Category
from podcastmanager.settings import AUDIOS_URL


class PlayerView(ListView):
    title = 'Player'
    template_name = 'player/index.html'

    def get_context_data(self, **kwargs):
        context = super(PlayerView, self).get_context_data(**kwargs)
        context['audio_list'] = self.queryset
        context['category_list'] = Category.objects.all()
        context['title'] = self.title
        return context

    def get_queryset(self):
        pm = PlayListManager()
        audio_list = []
        files_in_playlist = pm.get_files_in_playlist(folder=AUDIOS_URL)
        online_audios = Audio.objects.filter(filename__in=files_in_playlist)  # Returns unordered audio batch
        for file_name in files_in_playlist:
            try:
                audio_list.append(online_audios.get(filename=file_name))
            except ObjectDoesNotExist:
                pass
        self.queryset = audio_list
