#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.utils import timezone
from djcelery.models import PeriodicTask, IntervalSchedule
from mutagen import File
from datetime import datetime
from podcastmanager.settings import BASE_DIR, STATIC_ROOT, LIVE_COVERS_FOLDER, STATIC_URL
from django.core.exceptions import ObjectDoesNotExist
from django.core import urlresolvers
from django.contrib.contenttypes.models import ContentType
import os


class PlayHistory(models.Model):
    ini = models.DateTimeField("Inicio", null=True)
    end = models.DateTimeField("Fin", null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = (u'Historial de reproducciones')
        verbose_name_plural = verbose_name

    def stop(self):
        self.end = timezone.now()
        self.save()

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

class Categoria(models.Model):
    nombre = models.CharField("Nombre", max_length=250)
    max_reproducciones = models.PositiveIntegerField("Número de reproducciones totales", default=1)

    def get_associated_podcasts(self):
        return Podcast.objects.filter(categoria=self)

    def __unicode__(self):
        return self.nombre


class Podcast(models.Model):
    nombre  = models.CharField("Nombre del podcast", max_length=250, unique=False)
    descripcion = models.TextField("Descripción", blank=True)
    rssfeed = models.URLField("URL del feed RSS", unique=True)
    web = models.URLField("Página web")
    activo = models.BooleanField("¿Es un podcast activo actualmente?", default=True)
    categoria = models.ForeignKey(Categoria)
    # episode_active = models.IntegerField(blank=True,null=False,default=0)#,related_name='Episodio del podcast que suena o esta activo actualmente.')
    # episode_active = models.ForeignKey('Episode',null=True,default=None,related_name='Episodio del podcast que suena o esta activo actualmente.')
    # Episode Como string debido a la dependencia circular. related_name required.

    def __unicode__(self):
        return self.nombre



    # Asigna el numero maximo de reproducciones del porcas
    def set_max_repro(self, max_repro=1):
        self.max_play = max_repro
        self.save()

    # Asigna como el epidosio actual el pasado como parametro
    def set_active_episode(self, episode=None):
        if episode is not None:
            self.active_episode = episode
            self.save()

    # TODO: Calcular en meses el intervalo de tiempo que han estado sin publicar episodios
    # Si excede los 6 meses, se marcará como inactivo
    def set_active(self):
        pass

    def is_active(self):
        return self.activo

    def get_category(self):
        return self.categoria
        #return Categoria.objects.get(pk=self.categoria.id)

    def get_max_repro(self):
        return self.categoria.max_reproducciones

    def get_current_audio(self):
        current_audio = Episode.objects.get(pk=self.active_episode)
        if current_audio is not None:
            return current_audio
        return None

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    # TODO:  Implementar el borrado de imagenes cuyos episodios no están en la BBDD
    def remove_old_covers(self):
        id_episodio = 0
        try:
            if self.active_episode is not None:
                id_episodio = self.active_episode.id
        except ObjectDoesNotExist:
            print 'No active episode. Do you want I remove all audios?'
        print id_episodio
        related_episodes = Episode.objects.filter(podcast=self).exclude(pk=id_episodio)
        if not related_episodes.exists():
            print 'Nothing to do, nothing to remove.'
            return
        for episode in related_episodes:
            episode.remove_cover()

    # Elimina los archivos de audio relativos a sus episodios, menos el episodio activo
    def remove_old_files(self):
        try:
            if self.active_episode is None:
                return
        except ObjectDoesNotExist:
            print 'No active episode. Do you want I remove all audios?'
            return
        # IMPORTANTE. Esta operacion, se llevara a cabo siempre que los audios sean mas de 1
        # ya que podría haber inconsistencia en la BBDD, y borrar un audio que aun tenga que sonar.
        # Selecciona los audios de este podcast
        related_episodes = Episode.objects.filter(podcast=self)
        if related_episodes.count() > 1:
            # Y además, no pueder ser el actual.
            related_episodes = related_episodes.exclude(id=self.active_episode.id)
            if not related_episodes.exists():
                print 'Nothing to do, nothing to remove.'
                return
            for episode in related_episodes:
                # Borramos las covers antiguas
                episode.remove_cover()
                old_audio_file = episode.get_relative_path()
                if os.path.isfile(old_audio_file):
                    os.remove(old_audio_file)
                    if os.path.isfile(old_audio_file):
                        print('Unable to remove %s' % old_audio_file)
                    else:
                        print('Removed successfully %s' % old_audio_file)
# End Podcast


class Sound(models.Model):
    times_played = models.IntegerField(default=0)
    duration = models.FloatField(default=0)

    class Meta:
        abstract = True

    def play(self):
        ph = PlayHistory.objects.create(
            ini=timezone.now(),
            content_object=self
        )
        self.times_played += 1
        self.save()
        ph.save()
        return ph


class Episode(Sound):
    podcast = models.ForeignKey(Podcast)
    url = models.URLField(unique=False)
    titulo = models.CharField(max_length=250)
    #descripcion = models.TextField()
    _local_path = models.CharField(max_length=250)
    _filename = models.CharField(max_length=250)
    _date_published = models.DateTimeField(null=True, blank=True)
    _date_downloaded = models.DateTimeField(null=True, blank=True)
    _image_filename = models.CharField("Imagen", max_length=500)

    # HORRIBLE HACK
    DEFAULT_IMAGE = 'default.png'
    DEFAULT_EXT = '.jpg'
    RELATIVE_COVERS_DIR = STATIC_ROOT  + 'images/covers/'

    # Limitamos el título visible a 30 caracteres
    def short_name(self):
        if len(self.titulo) > 30:
            return str(self.titulo[:30] + ' ... ')
        else:
            return self.titulo

    def __unicode__(self):
        return unicode(self.titulo)

    # Checa si un episdio es el ultimo que ha estado sonado y que no haya terminado
    def has_not_finished(self):
        history = PlayHistory.objects.all()
        if history.count() < 1:
            return False
        last_entry = history.latest('ini')
        last_episode = last_entry.content_object
        if last_episode.get_file_name() == self._filename:
            return last_entry.end is None # Devolvera verdadero si no ha terminado
        return False

    def set_active(self):
        related_podcast = Podcast.objects.get(pk=self.podcast.id)
        related_podcast.active_episode = self
        related_podcast.save()

    def remove_file(self):
        if os.path.isfile(self.get_relative_path()):
            os.remove(self.get_relative_path())

    def remove_cover(self):
        if self._image_filename != self.DEFAULT_IMAGE:
            path = self.RELATIVE_COVERS_DIR + self._image_filename
            if os.path.isfile(path):
                os.remove(path)
                if os.path.isfile(path):
                    print 'Failed to remove old cover: %s' % path
                else:
                    print 'File removed successfully: %s' % path

    # Crea el thumbnail relacionado con cada audio visible en la lista de reproducción
    def create_cover(self):
        self._image_filename = self.DEFAULT_IMAGE
        self.save()
        if self._filename is None:
            print ('No audio in db: ' + self.__unicode__())
            return
        path_to_file = self._local_path + self._filename
        if not os.path.isfile(path_to_file):
            print ('No audio "%s" in path %s: ' % (self.__unicode__(), path_to_file))
            return
        try:
            audio = File(path_to_file)
            print 'Audio abierto'
            image_content = audio.tags['APIC:'].data
            if image_content is not None and len(image_content) > 0:
                print 'Hay ontenido'
                self._image_filename = self._filename + self.DEFAULT_EXT
                final_path = os.path.join(self.RELATIVE_COVERS_DIR, self._image_filename)
                print 'Final path ' + final_path
                # Check if a same-named file exists. If True, overwrite it.
                if os.path.isfile(final_path):
                    os.remove(final_path)
                with open(final_path, 'wb') as cover:
                    cover.write(image_content)
                    cover.close()
                    self.save()
        except:
            print 'Unable to create cover'

    def get_relative_path(self):
        return self._local_path + self._filename

    def get_local_path(self):
        return self._local_path

    def get_file_name(self):
        return self._filename

    def get_image_filename(self):
        return self._image_filename

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))
# End episodio

# Tras definir el "Episodio", resolvemos la dependencia circular con "Podcast" insertando la clave foranea
# ahora

Podcast.add_to_class(
    'active_episode',
    models.ForeignKey(Episode, default=0, null=True, blank=True, related_name='Episodio activo')
)
#
# (1 podcast, 1 episodio activo)


class Promotion(Sound):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    filename = models.FilePathField(max_length=250)
    num_play_cycle = models.IntegerField(default=1)

    def __unicode__(self):
        return self.name

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))


class TaskScheduler (models.Model):
    periodic_task = models.ForeignKey(PeriodicTask)

    @staticmethod
    def schedule_every(task_name, period, every, args=None,kwargs=None):
        """
        schedules a task by name every "every" "period". Example:
        TaskScheduler('mycustomtask','seconds',30,[1,2,3]) that would schedule your custom task run every 30 seconds
        with the arguments 1,2, and 3 passed to the actual task
        """

        permissible_periods = ['days', 'hours', 'minutes', 'seconds']
        if period not in permissible_periods:
            raise Exception ('Invalid period especified')
        #create periodic task and interval
        ptask_name="%s_%s"%(task_name,datetime.now())
        #create some name for the periodic task
        interval_schedules=IntervalSchedule.objects.filter(period=period, every=every)
        if interval_schedules:
            #just check if interval schedules exist like that already and reuse em
            interval_schedule=interval_schedules[0]
        else:
            #create a brand new interval schedule
            interval_schedule=IntervalSchedule()
            interval_schedule.every=every
            interval_schedule.period=period
            interval_schedule.save()
        ptask = PeriodicTask(name=ptask_name,task=task_name,interval=interval_schedule)
        if args:
            ptask.args = args
        if kwargs:
            ptask.kwargs = kwargs
        ptask.save()
        return TaskScheduler.objects.create(periodic_task=ptask)

    def stop(self):
        ptask = self.periodic_task
        ptask.enabled = False
        ptask.save()

    def start(self):
        ptask = self.periodic_task
        ptask.enabled = True
        ptask.save()

    def terminate(self):
        self.stop()
        ptask = self.periodic_task
        self.delete()
        ptask.delete()


from django.contrib.auth.models import Group
# Usuarios en directo. Tambien servira como registro. Se sabe que está un usuario en directo porque
# si el campo end_date es nulo o no esta definido.


class LiveEntry(models.Model):
    user = models.ForeignKey(User, limit_choices_to={'groups__name': 'podcasters'}, verbose_name='Podcaster emitiendo en directo')
    event_title = models.CharField(max_length=200, verbose_name='Titulo del evento')
    artist = models.CharField(max_length=200, verbose_name='Artista/s en directo')
    cover_file = models.CharField(max_length=200, null=True, verbose_name="Nombre del archivo que subieron")
    start_date = models.DateTimeField(verbose_name='Empezo a emitir')
    end_date = models.DateTimeField(null=True, verbose_name='Termino de emitir')

    # HORRIBLE HACK
    DEFAULT_IMAGE = 'default.png'

    def user_was_podcaster(self):
        try:
            pod_group = Group.objects.get(name='podcasters')
            return pod_group in self.user.groups
        except ObjectDoesNotExist:
            return False

    # Guarda covers de los usuarios live. Nombre imagen = nombreusuario_fecha.extension
    def handle_cover(self, cover_file):
        if cover_file is not None:
            extension = '.' + cover_file.name.split('.').pop()
            p_filename = self.user.username + '_' + datetime.now().strftime("%Y%m%d%H%M%S") + extension
            filename = os.path.join(STATIC_ROOT, LIVE_COVERS_FOLDER, p_filename)
            with open(filename, 'wb+') as destination:
                for chunk in cover_file.chunks():
                    destination.write(chunk)
                destination.close()
                if not destination.closed:
                    print 'Live user cover not closed.'
            return p_filename
        return None

    def get_image_file(self):
        if self.cover_file is None or len(self.cover_file) <= 0:
            return str(os.path.join(STATIC_URL, LIVE_COVERS_FOLDER, self.DEFAULT_IMAGE))
        else:
            return str(os.path.join(STATIC_URL, LIVE_COVERS_FOLDER, self.cover_file))

    class Meta:
        verbose_name = u'Live entries'
        verbose_name_plural = u'Live entries'



from mpc.models import MPDC
from podcastmanager.settings import CURRENT_PLAYLIST
# TODO FINISH THIS
class PlayListManager():

    old_audio = '' # Formato [audio_03.mp3]

    def __init__(self):
        mpc = MPDC()
        mpc.connect()
        self.client = mpc.client

    def status(self):
        return self.client.status()

    def __load__(self, playlist=CURRENT_PLAYLIST):
        print 'Cargando %s' % playlist
        self.client.load(playlist)

    def reset_playlist(self):
        print 'Reseteando playlist'
        self.client.clear()
        self.__load__()
        self.client.update()

    def add_song(self, file_name):
        real_path = BASE_DIR + '/audios/' + file_name
        if os.path.isfile(real_path):
            print 'File exists: ' + real_path
            try:
                self.client.add(file_name)
                print 'Added to playlist: %s' % real_path
            except:
                print 'Exception ocurred adding: %s' % real_path
        else:
            print 'No file %s in directory %s' % (file_name, (BASE_DIR + '/audios/'))

    def close(self):
        self.client.close()

    def play(self):
        self.client.repeat(1)
        print 'Looped playlist'
        self.client.play()

    def move(self, song_id):
        self.client.playid(song_id)

    def seek(self, song_id, time):
        self.client.seekid(song_id, time)

    def get_current_song(self):
        return self.client.currentsong()

    def get_current_song_time(self):
        return self.client.status()['time'].split(':')[0]

    def get_playlist_info(self):
        return self.client.playlistinfo()

    # Esta funcion se encarga se sumar +1 reproduccion al audio que empieza a sonar.
    # TODO Implementar
    #@task
    def refresh_repro(self):
        if self.client.status()['state'] == 'play':
            current_audio = self.client.currentsong()['file']
            if self.old_audio == '':
                # Significa que no ha habido audio anterior
                print 'No previous audio in PlayListManager'
                self.old_audio = current_audio
            elif current_audio != self.old_audio:
                try:
                    current_episode = Episode.objects.get(_filename=current_audio)
                except:
                    print 'This audio (%s) is currently sounding, ' \
                          'but does not have any episode associated' % current_audio
                    return
                finally:
                    current_episode.play()
                    self.old_audio = current_audio
            else:
                # Sigue sonando el mismo
                pass
