from django.contrib import admin
from models import *


class AdminEvent(admin.ModelAdmin):
    list_display = ('user', 'event_title', 'artists', 'first_tweet', 'started_at', 'ended_at', 'has_finished', 'thumbnail')
    readonly_fields = ('thumbnail',)
    ordering = ['-started_at']

    def has_finished(self, instance):
        return bool(instance.ended_at)
    has_finished.boolean = True

admin.site.register(Event, AdminEvent)