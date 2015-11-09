from django.contrib import admin

# Register your models here.
from models import Listener


class ListenerAdmin(admin.ModelAdmin):
    list_display = ('user_agent', 'ip', 'seconds_connected', 'hash')
    search_fields = ('user_agent', 'ip', 'hash')
    ordering = ['seconds_connected']



admin.site.register(Listener, ListenerAdmin)