#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User


class PlayHistory(models.Model):
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = 'Historial de reproducciones'
        verbose_name_plural = verbose_name

    def play(self):
        self.start_date = datetime.now()
        self.save()

    def stop(self):
        self.end_date = datetime.now()
        self.save()


class CategoryField(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Campos de categorías'
        verbose_name_plural = verbose_name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    #times_limit = models.PositiveIntegerField(default=1)
    parent_category = models.ForeignKey('self', null=True, blank=True)
    fields = models.ManyToManyField(CategoryField, through='CategoryFieldValue', null=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __unicode__(self):
        return self.name


class CategoryFieldValue(models.Model):
    category = models.ForeignKey(Category)
    category_field = models.ForeignKey(CategoryField)
    value = models.PositiveIntegerField()

    def __unicode__(self):
        return self.category.name + ", " + self.category_field.name

    class Meta:
        verbose_name = 'Valores de Campos de Categorías'
        verbose_name_plural = verbose_name


class Podcast(models.Model):
    title = models.CharField(max_length=200, unique=False, null=False)
    web_site = models.URLField(unique=False, null=True)
    rss_feed = models.URLField(unique=True, null=False)
    description = models.TextField(max_length=250, null=True, blank=True)
    active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, null=False)

    class Meta:
        verbose_name = 'Podcasters'
        verbose_name_plural = 'Podcasters'

    def __unicode__(self):
        return self.title


class Audio(models.Model):
    title = models.CharField(max_length=200)
    file_name = models.FileField(null=True, blank=True)
    times_played = models.PositiveIntegerField(default=0)
    description = models.TextField(max_length=500, null=True, blank=True)
    duration = models.FloatField(default=0)

    def __unicode__(self):
        return self.title


class Promotion(Audio):
    date_uploaded = models.DateTimeField(default=datetime.now())

    class Meta:
        verbose_name = 'Promo'
        verbose_name_plural = 'Promos'


class Episode(Audio):
    date_downloaded = models.DateTimeField(default=None)
    date_published = models.DateTimeField(default=None)
    podcast = models.ForeignKey(Podcast)

    class Meta:
        verbose_name = 'Episodio'
        verbose_name_plural = 'Episodios'

    def is_active(self):
        return self.times_played < self.podcast.category.times_limit

Podcast.add_to_class(
    'active_episode',
    models.ForeignKey(Episode, default=0, null=True, blank=True, related_name='Episodio activo')
)


class LiveEntry(models.Model):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    cover_file = models.FileField(upload_to='.')
    podcaster = models.ForeignKey(User)

