"""
WSGI config for budgettool project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

# from dev build
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budgettool.settings")

os.environ['DJANGO_SETTINGS_MODULE'] = 'budgettool.settings'

application = get_wsgi_application()
application = DjangoWhiteNoise(application)

#from https://devcenter.heroku.com/articles/django-memcache#further-reading-and-resources
# Fix django closing connection to MemCachier after every request (#11331)
from django.core.cache.backends.memcached import BaseMemcachedCache
BaseMemcachedCache.close = lambda self, **kwargs: None