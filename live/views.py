from django.contrib.auth.decorators import login_required
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView, CreateView
from django.http import JsonResponse, HttpResponseNotFound
from django.shortcuts import HttpResponseRedirect, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib.auth import login, logout
from django.core.urlresolvers import reverse_lazy
from .forms import *
from .decorators import podcaster_or_admin_member_required
from twitter import *
from podcastmanager.settings import TWITTER_ENABLED, TWITTER_OAUTH, BASE_DIR, LIVE_COVERS_FOLDER, DEFAULT_COVER_IMAGE
from playlist.models import PlayListManager
import logging
import os

# Logger for logging
logger = logging.getLogger(__name__)


# Some useful mixins


class PodcasterOrAdminMembershipRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(PodcasterOrAdminMembershipRequiredMixin, cls).as_view(**initkwargs)
        return podcaster_or_admin_member_required(view, login_url='/live/login/')


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view, login_url='/live/login/')


# Class-based views for this app


class IndexView(PodcasterOrAdminMembershipRequiredMixin, TemplateView):
    template_name = 'live/index.html'
    title = 'Live event'

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('is_online', False):
            return HttpResponseRedirect(reverse_lazy('on'))
        else:
            return super(IndexView, self).dispatch(request, *args, **kwargs)

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
        if is_anybody_online():
            context['event'] = last_event()
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated(): # You should not login twice
            return HttpResponseRedirect(self.get_success_url())
        elif is_anybody_online():
            return HttpResponseRedirect(reverse_lazy('wait'))
        else:
            return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super(LoginView, self).form_valid(form)


class WaitView(TemplateView):
    template_name = 'live/wait.html'
    context_object_name = 'event'
    title = 'Wait'

    def get_context_data(self, **kwargs):
        context = super(WaitView, self).get_context_data(**kwargs)
        context['title'] = self.title
        context['event'] = Event.objects.latest('started_at')
        context['default_cover'] = DEFAULT_COVER_IMAGE
        return context


class LogoutView(View):
    redirect_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('is_online', False):  # They came from the "on" page
            try:
                event = Event.objects.latest('started_at')
                event.ended_at = timezone.now()
                event.save()
            except Exception, e:
                logger.exception(e.message)
            finally:  # Replay
                resume_streaming()
        logout(request)
        return HttpResponseRedirect("%s?message=true" % self.redirect_url)


class LiveModeOn(PodcasterOrAdminMembershipRequiredMixin, TemplateView):
    template_name = 'live/on.html'
    title = 'Online'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('has_filled_the_form', False):
            return HttpResponseRedirect(reverse_lazy('index'))
        # If its the first time when the form has been filled
        if not request.session.get('is_online', False):
            request.session['is_online'] = True
            pause_streaming()
            if TWITTER_ENABLED:
                try:
                    event = Event.objects.latest('started_at')
                    tweet_event(event.first_tweet, event.get_cover())
                except Exception, e:
                    logger.exception(e.message)
        return super(LiveModeOn, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LiveModeOn, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context


class LiveModeOff(PodcasterOrAdminMembershipRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if request.session.get('is_online', False):  # They came from the "on" page
            try:
                event = Event.objects.latest('started_at')
                event.ended_at = timezone.now()
                event.save()
            except Exception, e:
                logger.exception(e.message)
            finally:  # Replay
                resume_streaming()
                # We re not online anymore
                try:
                    del request.session['is_online']
                    del request.session['has_filled_the_form']
                except KeyError:
                    logger.info('<is_online> key is not in session.')
                return HttpResponseRedirect(reverse_lazy('logout'))
        else:  # From anywhere else
            return HttpResponseRedirect(reverse_lazy('index'))


class TweetView(PodcasterOrAdminMembershipRequiredMixin, FormView):
    form_class = TweetForm

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            form = self.form_class(request.POST)
            if form.is_valid():
                tweet_event(tweet_content=form.cleaned_data.get('tweet'))
                return JsonResponse({'success': True})
            else:
                return HttpResponseNotFound(form.errors.as_json(), content_type='application/json')
        else:
            raise Http404


class EventCreateView(PodcasterOrAdminMembershipRequiredMixin, CreateView):
    model = Event
    fields = ['event_title', 'artists', 'cover', 'first_tweet']
    success_url = reverse_lazy('on')

    def dispatch(self, request, *args, **kwargs):
        view = super(EventCreateView, self).dispatch(request, *args, **kwargs)
        if not request.session.get('has_filled_the_form', False):
            request.session['has_filled_the_form'] = True
        return view

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(EventCreateView, self).form_valid(form)


def tweet_event(tweet_content='', cover_name=None):
    if len(tweet_content) > 0:
        tweet_content = tweet_content[:140]
        try:
            twitter_handler = Twitter(auth=OAuth(
                TWITTER_OAUTH['ACCESS_TOKEN'],
                TWITTER_OAUTH['ACCESS_TOKEN_SECRET'],
                TWITTER_OAUTH['CONSUMER_KEY'],
                TWITTER_OAUTH['CONSUMER_KEY_SECRET']
            ))
            # attaches the cover if possible
            if cover_name is not None and len(cover_name) > 0 and cover_name != DEFAULT_COVER_IMAGE:
                cover_name = os.path.basename(cover_name)
                cover_url = os.path.join(BASE_DIR, LIVE_COVERS_FOLDER, cover_name)
                with open(cover_url, 'rb') as cover_file:
                    image_data = cover_file.read()
                    # Upload cover image
                    t_up = Twitter(domain='upload.twitter.com', auth=OAuth(
                        TWITTER_OAUTH['ACCESS_TOKEN'],
                        TWITTER_OAUTH['ACCESS_TOKEN_SECRET'],
                        TWITTER_OAUTH['CONSUMER_KEY'],
                        TWITTER_OAUTH['CONSUMER_KEY_SECRET']
                    ))
                    id_img = t_up.media.upload(media=image_data)['media_id_string']
                    twitter_handler.statuses.update(status=tweet_content, media_ids=','.join([id_img, ]))
                    cover_file.close()
            else:
                twitter_handler.statuses.update(status=tweet_content)
        except Exception, e:
            logger.exception(e.message)


# Some helpers

def pause_streaming():
    try:
        pm = PlayListManager()
        if pm.status().get('state') == 'play':
            pm.pause()
        pm.close()
    except Exception, e:
        logger.info(e.message)


def resume_streaming():
    try:
        pm = PlayListManager()
        if pm.status().get('state') == 'pause':
            pm.play()
        pm.close()
    except Exception, e:
        logger.info(e.message)


def last_event():
    try:
        return Event.objects.latest('started_at')
    except ObjectDoesNotExist, e:
        return False


def is_anybody_online():
    try:
        return bool(Event.objects.latest('started_at').ended_at is None)
    except ObjectDoesNotExist, e:
        return False
