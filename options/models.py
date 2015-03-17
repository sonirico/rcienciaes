from django.db import models
from django.core.validators import RegexValidator
from tools.slugify import slugify

# Global config. Better here than inside each settings.py? We will see.


class Option(models.Model):
    name = models.CharField(max_length=50, null=False, verbose_name=u'Variable name')
    nice_name = models.CharField(
        max_length=50,
        null=False,
        verbose_name=u'Variable name',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]+$',
                message=u'Only alphanumeric chars allowed',
                code='invalid_variable'
            )
        ]
    )
    value = models.CharField(max_length=150, null=True, blank=True)
    auto_load = models.BooleanField(default=True, null=False)

    class Meta:
        verbose_name = u'Global settings'
        verbose_name_plural = verbose_name

    def save(self, *args, **kwargs):
        self.name = slugify(self.nice_name)
        super(Option, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.nice_name
