"""
This is a fake, empty app that exists so that we can use the Django test runner.

NB in order for this to run you will need django installed.
"""
import logging

from django.conf import settings

from django_inbound_email.signals import email_received

logger = logging.getLogger(__name__)

def on_email_received(sender, **kwargs):
    request = kwargs.pop('request', None)
    email = kwargs.pop('email', None)
    email.to = [email.from_email]
    email.from_email = email.to[0]
    email.send()

if settings.BOUNCEBACK_ENABLED:
    logger.info(u"Email bounceback feature is enabled.")
    email_received.connect(on_email_received)
