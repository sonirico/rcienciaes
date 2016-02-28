from playlist.models import *
import os
import string
import random


def get_name():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

def get_audios():
    return [
            'audios/geocastsemanalmay-20160215-200559.mp3',
            'audios/geocastsemanalmay-20160215-200559.mp3',
            'audios/kitarono-20160216-000307.mp3',
            'audios/kitarono-20160216-000307.mp3',
            'audios/kitarono-20160216-000307.mp3',
            'audios/kitarono-20160216-000308.mp3',
            'audios/kitarono-20160216-000308.mp3',
            'audios/kitarono-20160216-000309.mp3',
            'audios/kitarono-20160216-000309.mp3',
            'audios/kitarono-20160216-000310.mp3',
            'audios/kitarono-20160216-000310.mp3',
            'audios/kitarono-20160216-000310.mp3',
            'audios/kitarono-20160216-000311.mp3',
            'audios/kitarono-20160216-000311.mp3',
            'audios/kitarono-20160216-000311.mp3',
            'audios/kitarono-20160216-000312.mp3',
            'audios/kitarono-20160216-000312.mp3',
            'audios/kitarono-20160216-000312.mp3',
            'audios/kitarono-20160216-000313.mp3',
            'audios/kitarono-20160216-000313.mp3',
            'audios/kitarono-20160216-000313.mp3']


def do():
    d = '/home/podmanager/app/src'
    audios = get_audios()
    for e in Episode.objects.filter(filename__in=audios):
        path, ext = e.filename.name.split('.')
        old_name = e.filename.name
        new_name = path + get_name() + '.' + ext
        if os.path.isfile(os.path.join(d, old_name)):
            os.rename(os.path.join(d, old_name), os.path.join(d, new_name)) 
            e.filename.name = new_name
            e.save()
            print e, ', saved'
        else:
            print 'This one has an audio which does not exist', e

