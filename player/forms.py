#!/usr/bin/python
# -*- coding: utf-8 -*-

from django import forms


class LiveForm(forms.Form):
    image_file = forms.FileField(label='Imagen de portada', required=False)
    event_title = forms.CharField(max_length=200, label='Título del evento', required=True)
    artists = forms.CharField(max_length=200, label='Artista o conjunto de artistas', required=True)
    content = forms.CharField(widget=forms.Textarea(), max_length=140, label='Tweet', required=False)


class TweetForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea, max_length=140, required=True, label='Tweet')