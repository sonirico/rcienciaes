from django.shortcuts import render

# This class will parse our XML data
# Partially stolen from:
# https://github.com/beats-to/Icecast/blob/master/Icecast.py


class IcecastError(Exception):
    pass


class XMLParser():
    def __init__(self):
        # From JSON format
        self.attributes = []
