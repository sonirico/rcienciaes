#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf.urls import patterns
from playlist import views

urlpatterns = patterns('',
    (r'^refresh/$', views.tweet_new_audio)
)