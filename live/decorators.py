from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from .settings import GROUPS_REQUIRED


def podcaster_or_admin_member_required(view_func=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='/live/login/'):
    """
    Decorator for views that checks that the user is logged in and has a podcaster or administrator
    membership (or a superuser), displaying the login page if necessary.
    :param login_url:
    """
    return user_passes_test(
        lambda u: u.is_active and (u.groups.filter(name__in=GROUPS_REQUIRED).exists() or u.is_superuser),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )(view_func)