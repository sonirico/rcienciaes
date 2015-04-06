from django.conf.urls import patterns, include, url

from django.contrib import admin

#from player.views import *

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^api/', include('api.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^player/', include('player.urls', namespace="player")),
    url(r'^playlist/', include('playlist.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
