from django.conf.urls import url
from django.contrib.auth import views as auth_views
from .views import *


urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^login/wait/$', WaitView.as_view(), name='wait'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^password_change/$', auth_views.password_change, name='password_change'),
    url(r'^password_change/done/$', auth_views.password_change_done, name='password_change_done'),

    url(r'^create/$', EventCreateView.as_view(), name='event-create'),
    url(r'^on/$', LiveModeOn.as_view(), name='on'),
    url(r'^off/$', LiveModeOff.as_view(), name='off'),

    url(r'^on/tweet/$', TweetView.as_view(), name='tweet'),
]
