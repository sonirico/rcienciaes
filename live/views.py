from django.contrib.auth.decorators import login_required
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth import login, logout
from django.core.urlresolvers import reverse_lazy
from .forms import *


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view, login_url='/live/login/')


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'live/index.html'
    title = 'Live event'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data()
        context['title'] = self.title
        return context


class LoginView(FormView):
    template_name = 'live/login.html'
    title = 'Log-in'
    form_class = PodcasterLoginForm
    initial = {}
    success_url = reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super(LoginView, self).form_valid(form)


class LogoutView(View):
    redirect_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect(self.redirect_url)
