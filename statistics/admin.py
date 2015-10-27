from django.contrib import admin

# Register your models here.
from models import IceCastStatsEntry, Listener


class ListenerAdmin(admin.ModelAdmin):
    list_display = ('user_agent', 'ip', 'seconds_connected', 'hash')
    search_fields = ('user_agent', 'ip', 'hash')
    ordering = ['seconds_connected']


class IceCastStatEntryAdmin(admin.ModelAdmin):
    list_display = ('total_listeners', 'current_listeners', 'taken_at', 'history_entry')

admin.site.register(IceCastStatsEntry, IceCastStatEntryAdmin)
admin.site.register(Listener, ListenerAdmin)