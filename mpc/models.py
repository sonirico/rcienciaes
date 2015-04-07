#!/usr/bin/env python
# -*- coding: utf-8 -*-
import errno
from socket import error as socket_error
from mpd import MPDClient


class MPDCConnectionError(Exception):
    def __init__(self):
        print('MPD: Connection refused')


class MPDC():
    client = None
    settings = \
    {
        'server': 'localhost',
        'port': 6600,
        'timeout': 10,
        'idletimeout': 1,
        'use_unicode': True
    }

    def __init__(self):
        self.client = MPDClient()
        self.client.timeout = self.settings['timeout']
        self.client.idletimeout = self.settings['idletimeout']
        self.client.use_unicode = self.settings['use_unicode']

    def connect(self, server=None, port=None):
        if server is None:
            server = self.settings['server']
        if port is None:
            port = self.settings['port']
        try:
            self.client.connect(server, port)
        except socket_error as s_e:
            if s_e.errno == errno.ECONNREFUSED:
                # Connection refused. MPD is probably down.
                raise MPDCConnectionError
            return False
        return True
