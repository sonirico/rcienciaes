from podcastmanager.settings import COVERS_URL
from django.db.models.fields.files import FieldFile
from datetime import datetime
from normalize import normalize
from mutagen import File

import logging
import os


logger = logging.getLogger(__name__)


def file_cleanup(sender, instance, *args, **kwargs):
    """
        Deletes file(s) associated with a model instance. The model
        is not saved after deletion of the file(s) since this is meant
        to be used with the pre_delete signal.
    """
    instance.delete_files()


def make_cover(audio):
    """
        Get the associated image cover of each audio file. HACK: jpg
        :return
    """
    # TODO: change "cover" field from audios to podcasts when handling episodes.
    if audio is None:
        print("Null models instance might have no cover...")
        return
    logging.info('Creating audio for episode "%s"' % audio.title)
    path = audio.filename.name
    if os.path.isfile(path):
        try:
            audio_file = File(path)
            image_content = audio_file.tags['APIC:'].data
            if image_content is not None and len(image_content) > 0:
                cover_name = create_cover_name(audio)
                audio.cover.name = cover_name
                final_path = os.path.join(COVERS_URL, cover_name)
                if os.path.isfile(final_path):
                    os.remove(final_path)
                with open(final_path, 'wb') as cover:
                    cover.write(image_content)
                    cover.close()
                    audio.save()
        except Exception, e:
            logger.exception(e.message)
    else:
        print('This audio has no audio file. Probably it is not active either.')


def create_cover_name(audio):
    return normalize(audio.title) + '-' + datetime.now().strftime("%Y%m%d-%H%M%S") + ".jpg"


def calculate_duration(sender, instance, *args, **kwargs):
    if kwargs.get('created') is True:
        fields = instance.__dict__
        duration = fields.get('duration')
        if int(duration) == 0:
            new_duration = get_audio_duration(fields.get('filename'))
            if new_duration is not False:
                instance.duration = new_duration
                instance.save()


from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis


def get_audio_duration(filename):
    path = filename.name
    if os.path.isfile(path):
        ext = path.lower().split('.')[-1]
        audio = None
        if ext == 'mp3' or ext == 'mpeg':
            audio = MP3(path)
        elif ext == 'mp4' or ext == 'm4a':
            audio = MP4(path)
        elif ext == 'ogg':
            audio = OggVorbis(path)
        return audio.info.length
    return False