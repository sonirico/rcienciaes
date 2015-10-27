import requests
import logging
import xml.etree.ElementTree as ET
from django.shortcuts import render

from django.db import models
from requests.exceptions import ConnectionError
from settings import *
from django.core.exceptions import ObjectDoesNotExist
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

    def create_entry(self):
        self.set_stats()
        try:
            self.fields['history_entry'] = PlaylistHistory.objects.latest('started')
        except ObjectDoesNotExist, e:
            logger.exception(e.message)
        icecast_entry = IceCastStatsEntry(**self.fields)
        icecast_entry.save()


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

class IceCastStatsEntry(models.Model):
    total_listeners = models.PositiveIntegerField(default=0, verbose_name=u'Accumulative total listeners')
    current_listeners = models.PositiveIntegerField(default=0, verbose_name=u'Currently connected listeners')
    taken_at = models.DateTimeField(auto_now=False, auto_now_add=True, null=True, verbose_name=u'when this was picked up', editable=True)
    history_entry = models.ForeignKey(PlaylistHistory, null=True, verbose_name=u'Related history entry')

    class Meta:
        verbose_name = u'Every single stats entry'
        verbose_name_plural = u'Every single stats entry'

    def __unicode__(self):
        #return self.history_entry.audio.title
        return self.taken_at.strftime("%Y%m%d-%H%M%S")

