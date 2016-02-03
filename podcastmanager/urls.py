from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required

urlpatterns = [
    url(r'^api/', include('api.urls')),
    url(r'^live/', include('live.urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^player/', include('player.urls')),
    url(r'^playlist/', include('playlist.urls')),
    url(r'^stats/', include('statistics.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
