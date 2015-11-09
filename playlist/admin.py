from django.contrib import admin
from playlist.models import *
'''

from playlist.views import *
from django.contrib.contenttypes.models import ContentType
from playlist.models import Category as Categoria, Podcast, Episode, PlaylistHistory as PlayHistory, Promotion, LiveEntry

def elapsed_time(seconds, suffixes=['y','w','d','h','m','s'], add_s=False, separator=' '):
    time = []
    parts = [(suffixes[0], 60 * 60 * 24 * 7 * 52),
          (suffixes[1], 60 * 60 * 24 * 7),
          (suffixes[2], 60 * 60 * 24),
          (suffixes[3], 60 * 60),
          (suffixes[4], 60),
          (suffixes[5], 1)]
    seconds = int(round(seconds))
    # for each time piece, grab the value and remaining seconds, and add it to
    # the time string
    for suffix, length in parts:
        value = seconds / length
        if value > 0:
            seconds = seconds % length
            time.append('%s%s' % (str(value),(suffix, (suffix, suffix + 's')[value > 1])[add_s]))
        if seconds < 1:
            break
    return separator.join(time)
# Register your models here.


class PlayHistoryAdmin(admin.ModelAdmin):
    list_display = ['ini', 'end', 'Podcast', 'Audio', 'Reproducciones']
    ordering=['ini']

    def Audio(self,instance):
        object_type= instance.content_type.name
        if  object_type==u'episode':
            audio = Episode.objects.get(pk=instance.object_id)
            return audio
    def Podcast(self,instance):
        object_type= instance.content_type.name
        if  object_type==u'episode':
            podcast = Episode.objects.get(pk=instance.object_id).podcast
            return podcast
    def Reproducciones(self,instance):
        object_type= instance.content_type.name
        if  object_type==u'episode':
            times = Episode.objects.get(pk=instance.object_id).times_played
            return times


class EpisodeAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'Podcast', '_date_published','_date_downloaded', 'Duracion', 'times_played']
    ordering = ['-_date_downloaded']
    date_hierarchy = '_date_downloaded'

    def Podcast(self,instance):
        return Podcast.objects.get(pk=instance.podcast_id).nombre

    def Duracion(self,instance):
        return elapsed_time(instance.duration, separator=':')


class EpisodeInline(admin.StackedInline):
    model = Episode
    fields = ['times_played', '_filename']
    ordering = ['-_date_published']

class LiveEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'artist', 'event_title', 'cover_file', 'start_date', 'end_date']
    ordering = ['-start_date']

class PodcastAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rssfeed', 'web', 'activo', ]
    inlines = [EpisodeInline,]


from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.core.urlresolvers import reverse


class LogEntryAdmin(admin.ModelAdmin):

    date_hierarchy = 'action_time'

    readonly_fields = LogEntry._meta.get_all_field_names()

    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]


    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        'change_message',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = u'<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return link
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'

    def queryset(self, request):
        return super(LogEntryAdmin, self).queryset(request) \
            .prefetch_related('content_type')


#admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Categoria)
admin.site.register(Podcast, PodcastAdmin)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(PlayHistory, PlayHistoryAdmin)
admin.site.register(Promotion)
admin.site.register(LiveEntry, LiveEntryAdmin)


'''
from podcastmanager.settings import COVERS_URL
import os


class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded', 'expiration', 'promo_duration', 'tweet', 'category', 'is_active', 'thumbnail')
    date_hierarchy = 'uploaded'
    readonly_fields = ('thumbnail',)

    def is_active(self, instance):
        return instance.is_active()
    is_active.boolean = True

    def promo_duration(self, instance):
        m, s = divmod(instance.duration, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)
    promo_duration.short_description = u'Duration'


class PromoCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'interval', 'expire', 'days_to_expiration')

    def interval(self, instance):
        m, s = divmod(instance.time_interval, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)
    interval.short_description = u'Time lapse to be displayed at the playlist'


class PodcastCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'max_times_played', 'duration', 'days_to_expiration', 'days_to_inactive', 'podcast_count')

    def podcast_count(self, instance):
        return instance.podcast_set.count()

    def duration(self, instance):
        m, s = divmod(instance.max_duration, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)
    duration.short_description = u'Max duration'


class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'podcast', 'published', 'downloaded', 'custom_duration', 'times_played', 'active', 'thumbnail')
    search_fields = ('title',)
    ordering = ['-downloaded']
    date_hierarchy = 'downloaded'

    def custom_duration(self, instance):
        m, s = divmod(instance.duration, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)
    custom_duration.short_description = u'Duration'

    def active(self, instance):
        return instance.is_active()
    active.boolean = True


class EpisodeInline(admin.StackedInline):
    model = Episode
    fields = ['title', 'times_played', 'filename', 'cover']
    ordering = ['-published']

    def is_active(self, instance):
        return instance.is_active()
    is_active.boolean = True
    is_active.short_description = u'Active'


class PodcastAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description', 'feed', 'website', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'website',)
    inlines = [EpisodeInline,]


class PlaylistHistoryAdmin(admin.ModelAdmin):
    list_display = ('started', 'finished', 'podcast', 'audio', 'total_unique_listeners_count')
    ordering = ['-started']

    def podcast(self, instance):
        audio_type = instance.audio.get_type()
        if audio_type == u'episode':
            return instance.audio.podcast


admin.site.register(PodcastCategory, PodcastCategoryAdmin)
admin.site.register(PromoCategory, PromoCategoryAdmin)
admin.site.register(Podcast, PodcastAdmin)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Promotion, PromotionAdmin)
admin.site.register(PlaylistHistory, PlaylistHistoryAdmin)