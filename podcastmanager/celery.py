from __future__ import absolute_import
from celery import Celery
from django.conf import settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'podcastmanager.settings')
app = Celery('podcastmanager')
app.config_from_object('django.conf:settings')