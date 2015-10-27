import sys
import kronos
import random
import logging

from models import IceCastRetriever, IcecastListenersRetriever, Listener
from hashlib import md5

logger = logging.getLogger(__name__)

@kronos.register('* * * * *')
def stats_retriever():
    retriever = IceCastRetriever()
    retriever.create_entry()
    del retriever


@kronos.register('*/2 * * * *')
def update_listeners():
    retriever = IcecastListenersRetriever()
    listeners = retriever.listeners()  # Currently connected people
    if len(listeners) <= 0:
        return
    hashes = []
    for l in listeners:
        l_hash = create_hash(l)
        hashes.append(l_hash)
        l['hash'] = l_hash
    db_listeners = Listener.objects.filter(hash__in=hashes)
    if db_listeners.exists():
        # Update the ones which exists
        for l in listeners:
            if db_listeners.filter(hash=l.get('hash')).exists():
                logger.info('Current listeners recorded:', db_listeners.count())
                # Update
                listener = db_listeners[0]
                if int(l.get('seconds_connected')) > listener.seconds_connected:
                    listener.seconds_connected = int(l.get('seconds_connected'))
                    listener.save()
            else:
                # Create
                create_listener(l)
    else:
        # Create every one
        for l in listeners:
            create_listener(l)
    del retriever


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


def create_hash(listener):
    return md5(listener.get('ip') + listener.get('user_agent')).hexdigest()
