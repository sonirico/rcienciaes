from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Min, Max
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic import View, ListView
from models import IceCastStatsEntry
from forms import BetweenDatesForm

class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class StatsView(LoginRequiredMixin, ListView):
    template_name = 'statistics/index.html'
    title = 'Stats'
    model = IceCastStatsEntry
    queryset = IceCastStatsEntry.objects.order_by('-id')[:100]



def two_dates(request):
    if request.is_ajax():
        if request.method == 'POST':
            f = BetweenDatesForm(request.POST)
            if f.is_valid():
                c_data = f.cleaned_data
                start_date = c_data.get('start')
                end_date = c_data.get('end')
                print IceCastStatsEntry.objects.filter(taken_at__range=(start_date, end_date)).\
                    aggregate(Sum('current_listeners'))
                # TODO: Get stats
                return HttpResponse('{ "hello": "hi"}', content_type='application/json')
            else:
                print f.errors
    raise Http404


def between_dates(request):
    return render(request,
                  'statistics/between-dates.html',
                  {'title': "2 dates", 'form': BetweenDatesForm(initial={})}
    )