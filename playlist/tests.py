from django.test import TestCase
#from models import LiveUser
#from django.contrib.auth.models import User

'''
# Users in playlist_liveuser must be only in the podcasters group
class LiveUserTest(TestCase):
    def test_live_user_must_be_podcaster(self):
        no_podcaster = User.objects.create(username='nopodcaster')
        live_user = LiveUser(user=no_podcaster)
        self.assertEqual(live_user.user_was_podcaster(), False)
'''