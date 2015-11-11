from django.contrib.auth.forms import AuthenticationForm
from django.forms import ValidationError


class PodcasterLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super(PodcasterLoginForm, self).confirm_login_allowed(user)
        # Users must be podcasters or administrators
        user_groups = user.groups.all()
        is_podcaster = user_groups.filter(name='podcasters').exists()
        is_admin = user_groups.filter(name='administradores').exists()
        if bool(is_podcaster or is_admin) is False:
            raise ValidationError('You don\'t seem to be neither a podcaster nor an administrator member.')
