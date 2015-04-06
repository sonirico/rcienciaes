#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mpd import MPDClient


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
        self.client.connect(server, port)

#EOF
