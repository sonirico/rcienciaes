import re
import unicodedata

from django.utils import six
from django.utils.safestring import mark_safe
from django.utils.functional import allow_lazy


def slugify(value):
    """
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = value.decode('utf-8')
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return mark_safe(re.sub('[-\s]+', '_', value))
slugify = allow_lazy(slugify, six.text_type)


