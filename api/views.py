# -*- coding: utf-8 -*-

from django.shortcuts import Http404
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView

from statistics.models import IceCastRetriever

from live.models import Event
from live.views import is_anybody_online

from playlist.models import PlayListManager, Audio
from podcastmanager.settings import AUDIOS_URL

import logging
import os


logger = logging.getLogger(__name__)


class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        return context


class PlaylistManagerView(TemplateView):
    pm = None

    def __init__(self, *args, **kwargs):
        try:
            self.pm = PlayListManager()
            super(PlaylistManagerView, self).__init__(*args, **kwargs)
        except Exception, e:
            logger.exception(e.message)
            raise Http404

    def get(self, request, *args, **kwargs):
        return super(PlaylistManagerView, self).get(
            request, *args, **kwargs
        )


class ApiView(JSONResponseMixin, PlaylistManagerView):
    data = {}

    def __init__(self, *args, **kwargs):
        super(ApiView, self).__init__(*args, **kwargs)
        self.data = {}

    def render_to_response(self, context, **response_kwargs):
        return self.render_to_json_response(context, **response_kwargs)


class StatsView(ApiView):
    """
    Retrieves info about the current number of listeners
    """
    def get_data(self, context):
        try:
            retriever = IceCastRetriever()
            stats = retriever.raw_stats()
            del retriever
            return stats
        except Exception, e:
            logger.exception(e.message)
            raise Http404


class StatusView(ApiView):
    """
    Retrieves info about the status of the streaming.
        live: boolean,
        state: String [play|pause|stop]
        total_time: Integer,
        current_time: Integer,
        song: Integer
    """
    def __get_status(self):
        main_status = self.pm.status()
        self.data['live'] = is_anybody_online()
        self.data['state'] = main_status.get('state')
        if main_status.get('state') != 'stop':
            self.data['song'] = int(main_status.get('song'))
            self.data['current_time'], self.data['total_time'] = [int(v) for v in main_status.get('time').split(':')]
        return self.data

    def get_data(self, context):
        try:
            return self.__get_status()
        except Exception, e:
            self.data['message'] = e.message
        return self.data


class LiveView(ApiView):
    """
    Retrieves info about the current live event
        title :  String
        artists : String
        started_at : DateTime
        greet : String
        cover : String
    """
    def __event_data(self, event):
        self.data['title'] = event.event_title
        self.data['artists'] = event.artists
        self.data['started_at'] = str(event.started_at)
        self.data['greet'] = event.first_tweet
        self.data['cover'] = event.get_cover()
        if event.ended_at:
            self.data['ended_at'] = str(event.ended_at)
        return self.data

    def get_data(self, context):
        try:
            event = Event.objects.latest('started_at')
            return self.__event_data(event)
        except ObjectDoesNotExist, e:
            self.data['message'] = 'There have been no events so far'
            logger.exception(e.message)
        except Exception, e:
            logger.exception(e.message)
            self.data['message'] = 'Unexpected error'
        return self.data


class CurrentAudioFromMetadataView(ApiView):
    """
    Retrieves info about the current file from its metadata.
    """
    allowed_fields = ['album', 'title', 'genre', 'artist', 'time']

    def get_data(self, context):
        if self.pm.status().get('state') != 'stop':
            metadata = self.pm.get_current_song()
            a_f = self.allowed_fields[:]
            for k in metadata.keys():
                if k not in a_f:
                    del metadata[k]
            return metadata
        else:
            self.data['message'] = 'Streaming is currently stopped'
            return self.data


class CurrentAudioView(ApiView):
    """
    Retrieves info about the current audio file, from database
    """
    def get_data(self, context):
        try:
            file_name = self.pm.get_current_file()
            if not file_name:
                self.data['message'] = 'Streaming is currently stopped'
                return self.data
            else:
                audio = Audio.objects.get(filename=(os.path.join(AUDIOS_URL, file_name)))
                self.data = audio_serializer(audio)
        except ObjectDoesNotExist, e:
            del self.data
            self.data['message'] = 'It seems there is no info about the current audio'
            logger.exception(e.message)
        except Exception, e:
            del self.data
            self.data['message'] = 'Unexpected error'
            logger.exception(e.message)
        return self.data


class NextView(ApiView):
    """
    Retrieves info about the next audio. If <how_many> param is sent, the same amount of
    audios will be provided.
    """
    def get_data(self, context):
        if self.pm.status().get('state', False) != 'stop':
            next_song_pos = self.pm.status().get('nextsong')
            if self.kwargs.get('how_many', False):  # There is an amount
                amount = int(self.kwargs.get('how_many'))
                next_file = self.pm.get_playlist_info()[int(next_song_pos)].get('file')
                all_files = self.pm.get_files_in_playlist()
                all_files_copy = all_files[:]
                for f in all_files:
                    if f == next_file:
                        break
                    else:
                        all_files_copy.remove(f)
                search_files = [ AUDIOS_URL + filename for filename in all_files_copy[:amount] ]
                try:
                    del self.data
                    audio_list = []
                    for audio in Audio.objects.filter(filename__in=search_files):
                        audio_list.append(audio_serializer(audio))
                    self.data['playlist'] = audio_list
                    return self.data
                except Exception:
                    return {'message': 'Unable to see the next files'}
            else:
                next_file = self.pm.get_playlist_info()[int(next_song_pos)].get('file')
                try:
                    audio = Audio.objects.get(filename=(os.path.join(AUDIOS_URL, next_file)))
                    self.data = audio_serializer(audio)
                except ObjectDoesNotExist:
                    self.data['message'] = 'There are no records for the next audio'
            return self.data
        else:
            return {'message': 'Streaming seems to be stooped'}


class PlaylistView(ApiView):
    """
    Sends info about the entire playlist
    """
    def get_data(self, context):
        if self.pm.status().get('state', False) != 'stop':
            all_files_in_playlist = self.pm.get_files_in_playlist(AUDIOS_URL)
            self.data['playlist'] = []
            total_count = 0
            for f in all_files_in_playlist:
                try:
                    self.data['playlist'].append(audio_serializer(Audio.objects.get(filename=f)))
                    total_count += 1
                except ObjectDoesNotExist:
                    pass
            self.data['total_count'] = total_count
            return self.data
        else:
            return {'message': 'Streaming seems to be stooped'}


def audio_serializer(audio=None):
    """
    Audio info under customized keys
    :param audio: Audio Model Type
    :return: dict
    """
    if audio is None:
        return {}
    else:
        data = {}
        data['title'] = audio.title
        data['duration'] = audio.duration
        data['cover'] = audio.get_cover()
        data['type'] = audio_type = audio.get_type()
        if audio_type == 'episode':
            podcast = {}
            podcast['name'] = audio.podcast.name
            podcast['description'] = audio.podcast.description
            podcast['website'] = audio.podcast.website
            podcast['twitter'] = audio.podcast.twitter
            data['podcast'] = podcast
        return data



