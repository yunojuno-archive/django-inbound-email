"""
Simplest possible settings.py for use in running django-related unit tests.

This settings file would be completely useless for running a project, however
it has enough in it to be able to run the django unit test runner, and to spin
up django.contrib.auth users.

Please see online documentation for more details.
"""
# the HTTP request parser to use
INBOUND_EMAIL_PARSER = 'django_inbound_email.backends.sendgrid.SendGridRequestParser'

# whether to dump out a log of all incoming email requests
INBOUND_EMAIL_LOG_REQUESTS = False

# the max size (in Bytes) of any attachment to process
INBOUND_EMAIL_ATTACHMENT_SIZE_MAX = 10000000

ROOT_URLCONF = 'test_app.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'delme'
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_inbound_email',
    'test_app',
)

SECRET_KEY = "something really, really hard to guess goes here."

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}
