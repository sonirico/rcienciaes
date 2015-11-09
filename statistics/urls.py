from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^$', (StatsView.as_view()), name='stats'),
    url(r'^between-two-dates/$', BetweenTwoDates.as_view(), name='between-dates'),
    url(r'^past-few-days/$', InThePastDays.as_view(), name='past-days'),
    url(r'^listeners_per_month/$', UniqueListenersPerMonthJSONView.as_view(), name='listeners-per-month'),
    url(r'^listeners_per_day/$', UniqueListenersPerDayJSONView.as_view(), name='listeners-per-day'),
    url(r'^listeners_per_episode/$', UniqueListenersPerEpisode.as_view(), name='listeners-per-episode'),
    url(r'^podcast_stats/$', PodcastStatsView.as_view(), name='listeners-per-podcast'),

    # Not related with stats. Gets the thumbnail for each episode
    url(r'^podcast_thumbnail/(?P<podcast_id>\d+)/$', PodcastImageview.as_view(), name='get-podcast-image'),
]
