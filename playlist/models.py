# -*- coding: UTF-8 -*-

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models.signals import post_delete, post_save, pre_save
from django.core.exceptions import ObjectDoesNotExist
from django.core import urlresolvers

from random import shuffle

from polymorphic import PolymorphicModel

from colorful.fields import RGBColorField

from podcastmanager.settings import AUDIOS_URL, COVERS_URL, DEFAULT_COVER_IMAGE, REMOTE_COVERS_URI

from mpc.models import MPDC

from tools.filehandler import *


import logging
import os


logger = logging.getLogger(__name__)


class AdminBrowsableObject(models.Model):
    class Meta:
        abstract = True

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return urlresolvers.reverse(
            "admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,)
        )


class Category(PolymorphicModel, AdminBrowsableObject):
    name = models.CharField(max_length=100, verbose_name=u'Name of the category')
    slug = models.SlugField(max_length=120, editable=False, null=True, blank=True)
    color = RGBColorField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class PodcastCategory(Category):
    max_times_played = models.PositiveIntegerField(default=8, verbose_name=u'Max times to play (iterations)')
    max_duration = models.PositiveIntegerField(verbose_name=u'Max duration (seconds)')
    days_to_expiration = models.PositiveIntegerField(verbose_name=u'Last episode expiration (days)', default=90)
    days_to_inactive = models.PositiveIntegerField(
        verbose_name=u'Mark podcast as inactive after X days since its last episode',
        default=90)

    class Meta:
        verbose_name = u'Categories for Podcasts'
        verbose_name_plural = verbose_name


class PromoCategory(Category):
    time_interval = models.PositiveIntegerField(
        verbose_name=u'Time lapse for being displayed on the playlist (seconds)')
    expire = models.BooleanField(default=False, verbose_name=u'Does this kind of promos expire?')
    days_to_expiration = models.PositiveIntegerField(verbose_name=u'How long make promos expire (days)', default=90)

    class Meta:
        verbose_name = u'Categories for Promos'
        verbose_name_plural = verbose_name


class Audio(PolymorphicModel, AdminBrowsableObject):
    title = models.CharField(max_length=250, verbose_name=u'Title of the audio')
    duration = models.PositiveIntegerField(default=0, null=True, verbose_name=u'Duration (seconds)')
    filename = models.FileField(upload_to=AUDIOS_URL, verbose_name=u'Audio file')
    cover = models.ImageField(null=True, blank=True, upload_to=COVERS_URL)
    times_played = models.PositiveIntegerField(default=0, verbose_name=u'Times played')

    def play(self):
        history_entry = PlaylistHistory(audio=self)
        history_entry.save()
        self.times_played += 1
        self.save()
        return history_entry

    def stop(self):
        pass

    def get_color(self):
        pass

    def tweet_title(self):
        if len(self.title) > 130:
            return self.title[:120] + '...'
        return self.title

    def short_title(self):
        """
            Limit title length to a hardcoded number when displaying on views
            :return: Formatted title
        """
        if len(self.titulo) > 30:
            return str(self.titulo[:30] + ' ... ')
        else:
            return self.titulo

    def thumbnail(self):
        """
        Not a fan of this
        :return:
        """
        if len(self.cover.name) > 1:
            return u'<img src="/%s" title="%s" with="32" height="32" />' % (
                os.path.join(COVERS_URL, self.get_cover()),
                self.title
            )
        else:
            return 'Sin cover'
    thumbnail.allow_tags = True

    def get_cover(self):
        """
        :return: String. File name of the image of the audio
        """
        if self.cover is not None and len(self.cover.name) > 0:
            return os.path.basename(self.cover.name)
        else:
            return False

    def get_remote_cover_uri(self):
        cover_name = self.get_cover()
        if not cover_name:
            return None
        else:
            return os.path.join(REMOTE_COVERS_URI, cover_name)

    def get_filename(self):
        """
            Since filename field stores the relative path of the audio file,
            we have to separate it from its parent folder
        :return: Original name
        """
        if self.filename is not None and len(self.filename.name) > 0:
            return os.path.basename(self.filename.name)
        else:
            return False

    def get_category_name(self):
        if self.get_type() == 'episode':
            return 'episode'
        else:
            return unicode(self.category.name)

    def get_type(self):
        # Yes, I prefer this instead of using ContentType library. Problem?
        return self.__class__.__name__.lower()

    def last_played_at(self):
        try:
            plh = self.playlisthistory_set.latest('started')
            return plh
        except ObjectDoesNotExist:
            return False
            # PlaylistHistory.objects.all

    def get_category(self):
        pass

    def is_active(self):
        """
            @Overriden
            :return:
        """
        pass

    def delete_files(self):
        self.delete_audio()
        self.delete_cover()

    def delete_audio(self):
        if self.filename and len(self.filename.name) > 0:
            if os.path.isfile(self.filename.name):
                logger.info('Erasing audio file: ' + self.filename.name)
                os.remove(self.filename.name)
                self.filename.name = ''
                self.save()

    def delete_cover(self):
        if self.cover and len(self.cover.name) > 0 and self.cover.name != DEFAULT_COVER_IMAGE:
            name = os.path.basename(self.cover.name)
            relative_path = os.path.join(COVERS_URL, name)
            if os.path.isfile(relative_path):
                os.remove(relative_path)
                logger.info('Erasing cover file: ' + self.cover.name)
        self.cover.name = DEFAULT_COVER_IMAGE
        self.save()

    def __unicode__(self):
        return self.title


class Podcast(AdminBrowsableObject):
    name = models.CharField(max_length=250, verbose_name=u'Podcast title')
    description = models.TextField(max_length=512, verbose_name=u'Short description', blank=True, null=True)
    feed = models.URLField(verbose_name=u'Feed RSS', unique=True)
    website = models.URLField(verbose_name=u'Podcaster\'s website')
    twitter = models.CharField(verbose_name=u'Twitter account', null=True, blank=True, max_length=32)
    active = models.BooleanField(default=True)

    category = models.ForeignKey(PodcastCategory, default=1)

    def get_cover(self):
        for episode in self.episode_set.all().order_by('-downloaded'):
            if episode.get_cover() != DEFAULT_COVER_IMAGE:
                return episode.get_cover()
        return DEFAULT_COVER_IMAGE

    def deactivate_all(self):
        for episode in self.episode_set.all():
            episode.active = False
            episode.save()

    def get_max_duration(self):
        return self.category.max_duration

    def get_next_episode(self):
        """
        :return: Next episode object to be played. Between the less played, we have to choose randomly
        """
        episodes = self.episode_set.all()
        times_played_aux_set = [e.times_played_aux for e in episodes]
        if len(times_played_aux_set) > 0:
            episode_list = list(episodes.filter(times_played_aux=min(times_played_aux_set)))
            shuffle(episode_list)
            return episode_list[0]
        else:
            return False

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'Podcast'
        verbose_name_plural = u'Podcasts'


class Episode(Audio):
    uri = models.URLField(verbose_name=u'File internet location', null=True, blank=True)
    published = models.DateTimeField(
        null=True, blank=True, auto_now=False, auto_now_add=False, verbose_name=u'Date released'
    )
    downloaded = models.DateTimeField(auto_now=False, auto_now_add=True, verbose_name=u'Date downloaded')
    times_played_aux = models.IntegerField(
            default=0, blank=False, null=False, verbose_name=u'Crucial for recalculating next episode'
    )
    podcast = models.ForeignKey(Podcast)


    class Meta:
        verbose_name = u'Episode'
        verbose_name_plural = u'Episodes'

    def set_active(self):
        self.podcast.active_episode = self
        self.podcast.save()
        self.save()

    def get_category(self):
        return self.podcast.category

    def get_color(self):
        return self.podcast.category.color

    def is_active(self):
        """
            This kind of episodes are always active
        :return: True
        """
        return True

    def play(self):
        self.times_played_aux += 1
        self.save()

        return super(Episode, self).play()

    def is_duplicated(self, episode_item):
        # TODO: Use a dict and a for statement for this:
        if episode_item.get('uri') == self.uri:
            return True
        if episode_item.get('filename') == self.filename.name:
            return True
        if episode_item.get('published') == self.published:
            return True
        if episode_item.get('title') == self.title:
            return True
        return False

    @staticmethod
    def set_min_times_played_value(sender, instance, *args, **kwargs):
        if kwargs.get('created') is True:
            episode_set = instance.podcast.episode_set.exclude(pk=instance.pk)
            logger.info('Calculating times_played_aux for {}'.format(instance))
            if episode_set.count() > 0:
                ep_list = [e.times_played_aux for e in episode_set.all()]
                if len(ep_list) > 0:
                    instance.times_played_aux = min([e.times_played_aux for e in episode_set.all()])
                    logger.info("Set to %s" % instance.times_played_aux)
            else:
                instance.times_played_aux = 0
                logger.info("Set to 0")
            instance.save()


Podcast.add_to_class(
    'active_episode',
    models.ForeignKey(Episode, on_delete=models.SET(None), default=None, null=True, blank=True, related_name=u'active_episode')
)


class Promotion(Audio):
    uploaded = models.DateTimeField(auto_now=False, auto_now_add=True, verbose_name=u'Registration date')
    expiration = models.DateTimeField(
        null=True, blank=True, auto_now=False, auto_now_add=False, verbose_name=u'When does it expire?'
    )
    tweet = models.TextField(max_length=140, verbose_name=u'Associated tweet', null=True, blank=True)
    category = models.ForeignKey(PromoCategory)

    class Meta:
        verbose_name = u'Promo'
        verbose_name_plural = u'Promos'

    def get_interval(self):
        return self.category.time_interval

    def get_category(self):
        return self.category

    def get_color(self):
        return self.category.color

    def is_active(self):
        # Scheduled Expiration date?
        if self.expiration is not None:
            days = (timezone.now() - self.expiration).days
        # Does it expire?
        elif bool(self.get_category().expire):
            days = (timezone.now() - self.uploaded).days
        else:
            return True
        if days >= self.get_category().days_to_expiration:
            return False
        return True


class PlaylistHistory(AdminBrowsableObject):
    started = models.DateTimeField(auto_now_add=True, auto_now=False)
    finished = models.DateTimeField(auto_now_add=False, auto_now=False, null=True)
    audio = models.ForeignKey(Audio, null=True, blank=True)
    total_unique_listeners_count = models.PositiveIntegerField(default=0, verbose_name=u'Unique listeners count')

    class Meta:
        verbose_name = u'Playlist history record'
        verbose_name_plural = u'Playlist history records'

    def stop(self):
        self.finished = timezone.now()
        self.total_unique_listeners_count = self.listenersforhistory_set.count()
        self.save()

    def __unicode__(self):
        return unicode('Recorded <%s>' % self.audio.title)





class PlayListManager(object):
    old_audio = ''  # Formato [audio_03.mp3]

    def __init__(self):
        mpc = MPDC()
        mpc.connect()
        self.client = mpc.client

    def status(self):
        return self.client.status()

    def __load__(self, playlist='current'):
        logger.info('Loading new playlist: %s' % playlist)
        self.client.load(playlist)

    def reset_playlist(self):
        logger.info('Reseting playlist')
        self.client.clear()
        self.client.update()
        self.__load__()

    def add_song(self, file_name):
        real_path = os.path.join(AUDIOS_URL, file_name)
        if os.path.isfile(real_path):
            try:
                self.client.add(file_name)
                logger.info('Song added: %s' % file_name)
            except Exception, e:
                logger.exception(e.message)

    def close(self):
        self.client.close()

    def pause(self):
        logger.info('Pausing streaming')
        self.client.pause()

    def play(self):
        logger.info('Playing/Resuming streaming')
        self.client.repeat(1)
        self.client.play()

    def move(self, song_id):
        self.client.playid(song_id)

    def seek(self, song_id, time):
        logger.info('Moving to song %s at time %s' % (song_id, time))
        self.client.seekid(song_id, time)

    def get_current_file(self):
        if self.status().get('state') != 'stop':
            return self.get_current_song().get('file', False)
        return False

    def get_current_song(self):
        return self.client.currentsong()

    def get_current_song_time(self):
        if self.client.status().get('state') != 'stop':
            return self.client.status().get('time').split(':')[0]
        else:
            return 0

    def get_playlist_info(self):
        return self.client.playlistinfo()

    def get_files_in_playlist(self, folder=None):
        if folder is None or len(folder) < 1:
            return list(audio_file.get('file') for audio_file in self.client.playlistinfo())
        else:
            return list((folder + audio_file.get('file')) for audio_file in self.client.playlistinfo())





# Signals. IT IS HIGHLY recommended put this at the end of the file
post_save.connect(Episode.set_min_times_played_value, sender=Episode)


post_save.connect(calculate_duration, sender=Promotion)
post_save.connect(calculate_duration, sender=Episode)



# Delete linked files, such as audios or covers
post_delete.connect(file_cleanup, sender=Episode)
post_delete.connect(file_cleanup, sender=Promotion)
