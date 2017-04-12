from os import environ, getenv

DEBUG = True
# # if we have an email server setup, then the test app will listen for incoming
# # emails, and send them back to the sender. This requires a set of valid SMTP
# # settings:
# try:
#     EMAIL_HOST = environ['EMAIL_HOST']
#     EMAIL_HOST_USER = environ['EMAIL_HOST_USER']
#     EMAIL_HOST_PASSWORD = environ['EMAIL_HOST_PASSWORD']
#     EMAIL_PORT = int(environ.get('EMAIL_PORT', 587))
#     EMAIL_USE_TLS = environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
#     BOUNCEBACK_ENABLED = True

# except KeyError as e:
#     print("Missing SMTP server environment settings, bounceback is disabled: %s" % e)
#     BOUNCEBACK_ENABLED = False

# # set the django DEBUG option
# DEBUG = getenv('DJANGO_DEBUG', 'true').lower() == 'true'

# the HTTP request parser to use - we set a default as the tests need a valid parser.
INBOUND_EMAIL_PARSER = environ.get(
    'INBOUND_EMAIL_PARSER',
    'django_inbound_email.backends.sendgrid.SendGridRequestParser'
)

# The authentication key provided by Mandrill. If supplied, the
# X-Mandrill-Signature header on the request will be verified during parsing.
INBOUND_MANDRILL_AUTHENTICATION_KEY = environ.get('INBOUND_EMAIL_PARSER')

# whether to dump out a log of all incoming email requests
INBOUND_EMAIL_LOG_REQUESTS = environ.get('INBOUND_EMAIL_LOG_REQUESTS', 'false').lower() == 'true'

# the max size (in Bytes) of any attachment to process - defaults to 10MB
INBOUND_EMAIL_ATTACHMENT_SIZE_MAX = int(environ.get('INBOUND_EMAIL_ATTACHMENT_SIZE_MAX', 10000000))

ROOT_URLCONF = 'inbound_email.urls'

# this isn't used, but Django likes having something here for running the tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

INSTALLED_APPS = (
    'inbound_email',
)

# none required, but need to explicitly state this for Django 1.7
MIDDLEWARE_CLASSES = []

SECRET_KEY = "something really, really hard to guess goes here."


USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGE_CODE = getenv('DEFAULT_LANGUAGE_CODE', 'en-gb')

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
            'level': 'INFO',
        },
    }
}

assert DEBUG is True, "This settings file is for local testing only."
