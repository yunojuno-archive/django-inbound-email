"""Test app settings.

The test_app project is primarily used for running the django_inbound_email
tests within a Django project, however, this settings file does allow for a
secondary set of 'real-world' tests. If the environment settings allow, the
test_app will use the django_inbound_email app to listen for incoming
messages, which it will bounceback to the sender.

In addition, the top-level requirements.txt and Procfile files allow for the
project to be deployed, as-is, to Heroku for real-world testing.

If you have an Heroku account, it's as simple as:

    # pull the latest source and cd into the directory
    $ git pull git@github.com:yunojuno/django-inbound-email.git
    $ cd django-inbound-email
    # create a new Heroku app, set the parser to use.
    django-inbound-email$ heroku create
    django-inbound-email$ heroku config:set INBOUND_EMAIL_PARSER=path.to.parser
    # push latest master to new Heroku app
    django-inbound-email$ git push heroku master:master

If the app created by Heroku is called "safe-earth-8826", then you will now
have an inbound handler on http://safe-earth-8826.herokuapp.com/emails/inbound/
You can either POST direct to this handler (e.g. using the Postman chrome app),
or even configure your email handler and try some real tests.

NB It uses the Django dev server to serve the requests - I hope I don't need to
point out that this is in no way sufficient to run a production application. You
run this app at your own risk.

"""
from os import environ, getenv

# if we have an email server setup, then the test app will listen for incoming
# emails, and send them back to the sender. This requires a set of valid SMTP
# settings:
try:
    EMAIL_HOST = environ['EMAIL_HOST']
    EMAIL_HOST_USER = environ['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD = environ['EMAIL_HOST_PASSWORD']
    EMAIL_PORT = int(environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
    BOUNCEBACK_ENABLED = True

except KeyError as e:
    print(u"Missing SMTP server environment settings, bounceback is disabled: %s" % e)
    BOUNCEBACK_ENABLED = False

# set the django DEBUG option
DEBUG = getenv('DJANGO_DEBUG', 'true').lower() == 'true'

# the HTTP request parser to use - we set a default as the tests need a valid parser.
INBOUND_EMAIL_PARSER = environ.get(
    'INBOUND_EMAIL_PARSER',
    'django_inbound_email.backends.sendgrid.SendGridRequestParser'
)

# whether to dump out a log of all incoming email requests
INBOUND_EMAIL_LOG_REQUESTS = environ.get('INBOUND_EMAIL_LOG_REQUESTS', 'false').lower() == 'true'

# the max size (in Bytes) of any attachment to process - defaults to 10MB
INBOUND_EMAIL_ATTACHMENT_SIZE_MAX = int(environ.get('INBOUND_EMAIL_ATTACHMENT_SIZE_MAX', 10000000))

ROOT_URLCONF = 'test_app.urls'

# this isn't used, but Django likes having something here for running the tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

INSTALLED_APPS = (
    'inbound_email',
    'test_app',
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
