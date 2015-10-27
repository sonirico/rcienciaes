from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from podcastmanager.settings import STATIC_URL, LIVE_COVERS_FOLDER
import os


class LiveEntry(models.Model):
    user = models.ForeignKey(User, limit_choices_to={'groups__name': 'podcasters'}, verbose_name='Podcaster emitiendo en directo')
    event_title = models.CharField(max_length=200, verbose_name='Titulo del evento')
    artist = models.CharField(max_length=200, verbose_name='Artista/s en directo')
    cover_file = models.CharField(max_length=200, null=True, verbose_name="Nombre del archivo que subieron")
    start_date = models.DateTimeField(verbose_name='Empezo a emitir')
    end_date = models.DateTimeField(null=True, verbose_name='Termino de emitir')

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
            #TODO: solve static root issue
            filename = None
            #filename = os.path.join(STATIC_ROOT, LIVE_COVERS_FOLDER, p_filename)
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
        verbose_name = u'Registros del modo Live'
        verbose_name_plural = verbose_name