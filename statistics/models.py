import requests
import logging
import xml.etree.ElementTree as ET
from django.db import models
from requests.exceptions import ConnectionError
from settings import *
from playlist.models import PlaylistHistory
# This class will parse our XML data
# Partially stolen from:
# https://github.com/beats-to/Icecast/blob/master/Icecast.py
logger = logging.getLogger(__name__)


class IcecastError(Exception):
    pass

# Fields whose value will be retrieved from Icecast

fields = {
    'current_listeners': 'listeners',  # The number of currently connected
    'total_listeners': 'listener_connections'  # Accumulative total listeners
}


class IceCastRetriever(object):

    errors = {
        400: 'Bad request',
        401: 'Unauthorized. Authentication failed',
        403: 'Forbidden',
        404: 'Not found',
        500: 'Internal server error',
        502: 'Bad gateway'
    }

    def __init__(self):
        self.uri = URI_FORMAT.format(HOST, PORT, URL_MAIN_STATS)
        self.parser = None
        self.fields = None
        self.connect()

    def connect(self):
        try:
            req = requests.get(self.uri, auth=(USER, PASSWORD), headers=HEADERS, timeout=HTTP_TIMEOUT,)
        except ConnectionError:
            raise IcecastError('Unable to make request')
        if req.status_code != 200:
            if req.status_code in self.errors:
                raise IcecastError(self.errors[req.status_code])
            else:
                raise IcecastError('Unimplemented error')
        try:
            self.parser = ET.fromstring(req.text)
            self.fields = fields.copy()
        except:
            raise IcecastError("Error parsing xml")

    def set_stats(self):
        try:
            for field in self.fields:
                self.fields[field] = int(self.parser.find(self.fields[field]).text)
        except Exception, e:
            logger.exception(e.message)

    def raw_stats(self):
        self.set_stats()
        return self.fields




class IcecastListenersRetriever(IceCastRetriever):
    listener_fields = {
        'IP': 'ip',
        'ID': 'id',
        'UserAgent': 'user_agent',
        'Connected': 'seconds_connected'
    }

    def __init__(self):
        self.uri = URI_FORMAT.format(HOST, PORT, URL_LIST_CLIENTS)
        self.parser = None
        self.connect()

    def listeners(self):
        listener_list = []
        for listener in self.parser.iter('listener'):
            l = {}
            for k, v in self.listener_fields.iteritems():
                l[v] = listener.find(k).text
            listener_list.append(l)
        return listener_list


class Listener(models.Model):
    ip = models.GenericIPAddressField(verbose_name='IP Address', protocol='both', null=True, blank=True)
    user_agent = models.CharField(verbose_name='User Agent', null=True, blank=True, max_length=256)
    seconds_connected = models.PositiveIntegerField(verbose_name='Seconds connected')
    hash = models.CharField(verbose_name='Unique Hash', db_index=True, max_length=32)

    def __unicode__(self):
        return self.hash


class ListenersForHistory(models.Model):
    entry_history = models.ForeignKey(PlaylistHistory, verbose_name=u'Playlist history entry')
    listener_hash = models.CharField(verbose_name=u'Unique Hash', max_length=32, db_index=True)
    taken_at = models.DateTimeField(verbose_name=u'When has it been recorded', auto_now=False, auto_now_add=True)

    def __unicode__(self):
        return self.entry_history.audio.title