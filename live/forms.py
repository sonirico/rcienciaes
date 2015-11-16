from django.contrib.auth.forms import AuthenticationForm
from django import forms
from .models import Event


class TweetForm(forms.Form):
    tweet = forms.CharField(max_length=140, min_length=5)


class PodcasterLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super(PodcasterLoginForm, self).confirm_login_allowed(user)
        # Users must be podcasters or administrators
        user_groups = user.groups.all()
        is_podcaster = user_groups.filter(name='podcasters').exists()
        is_admin = user_groups.filter(name='administradores').exists()
        if bool(is_podcaster or is_admin) is False:
            raise forms.ValidationError('You don\'t seem to be neither a podcaster nor an administrator member.')


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['user', 'event_title', 'artists', 'cover', 'first_tweet']
