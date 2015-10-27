from views import *
from django.conf.urls import url
from django.contrib.auth.decorators import login_required


urlpatterns = [
    url(r'^$', (StatsView.as_view()), name='stats'),
    url(r'^between-dates/$', between_dates),
    url(r'^between-dates/two-dates/$', two_dates),
]
