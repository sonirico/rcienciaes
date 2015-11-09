import sys
import kronos
import random
import logging

from playlist.models import PlaylistHistory
from models import IceCastRetriever, IcecastListenersRetriever, Listener, ListenersForHistory
from hashlib import md5

logger = logging.getLogger(__name__)


@kronos.register('* * * * *')
def count_unique_listeners():
    retriever = IcecastListenersRetriever()
    listeners = retriever.listeners()  # Obtains currently connected people
    if len(listeners) < 1:
        return
    for listener in listeners:
        l_hash = create_hash(listener)
        listener['hash'] = l_hash
    current_record = PlaylistHistory.objects.latest('started')
    recorded_listeners = ListenersForHistory.objects.filter(entry_history=current_record)
    # is there someone recorded already ? Update the already recorded. Create the new ones.
    if recorded_listeners.exists():
        for listener in listeners:
            old_listeners = recorded_listeners.filter(listener_hash=listener.get('hash'))
            if not old_listeners.exists():  # Create
                create_listener(listener)
                create_listener_history(current_record, listener)
            else:
                update_listener(listener)
    else:  # Must add the new ones
        for listener in listeners:
            create_listener(listener)
            create_listener_history(current_record, listener)
    del retriever



def create_listener_history(ph_recorded, listener):
    try:
        ListenersForHistory(
            entry_history=ph_recorded,
            listener_hash=listener.get('hash')
        ).save()
    except Exception, e:
        logger.exception(e.message)

def create_listener(listener_dict):
    logger.info('Creating listener')
    if listener_dict.get('id'):
        del listener_dict['id']
    try:
        listener_dict['seconds_connected'] = int(listener_dict.get('seconds_connected'))
        db_l = Listener(**listener_dict)
        db_l.save()
    except Exception, e:
        logger.exception(e.message)


def update_listener(listener_dict):
    if listener_dict.get('id'):
        del listener_dict['id']
    try:
        seconds = int(listener_dict.get('seconds_connected'))
        listeners_db = Listener.objects.filter(
            hash=listener_dict.get('hash'),
            seconds_connected__lt=seconds
        )
        if listeners_db.exists():
            listeners_db.update(seconds_connected=seconds)
    except Exception, e:
        logger.exception(e.message)


def create_hash(listener):
    return md5(listener.get('id') + listener.get('ip') + listener.get('user_agent')).hexdigest()
