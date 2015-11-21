from django.db import models
from django.contrib.auth.models import User
from podcastmanager.settings import LIVE_COVERS_FOLDER, DEFAULT_COVER_IMAGE, COVERS_URL
import os


class Event(models.Model):
    user = models.ForeignKey(User, verbose_name=u'Podcaster emitiendo en directo')
    event_title = models.CharField(max_length=200, verbose_name=u'Titulo del evento')
    artists = models.CharField(max_length=200, verbose_name=u'Artista/s en directo')
    first_tweet = models.CharField(max_length=140, verbose_name=u'Tweet content', null=True, blank=True)
    cover = models.ImageField(null=True, blank=True, upload_to=LIVE_COVERS_FOLDER, default=DEFAULT_COVER_IMAGE)
    started_at = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name=u'Empezo a emitir')
    ended_at = models.DateTimeField(null=True, verbose_name=u'Termino de emitir', blank=True)

    class Meta:
        verbose_name = u'Live entries'
        verbose_name_plural = verbose_name

    def get_cover(self):
        """
        :return: String. File name of the image of the event
        """
        if self.cover is not None and len(self.cover.name) > 0:
            return os.path.basename(self.cover.name)
        else:
            return False

    def thumbnail(self):
        """
        Not a fan of this
        :return:
        """
        return u'<img src="/%s" title="%s" with="32" height="32" />' % (
            os.path.join(LIVE_COVERS_FOLDER, self.get_cover()),
            self.event_title
        )
    thumbnail.allow_tags = True

    def __unicode__(self):
        return '%s de, %s' % (self.event_title, self.artists)