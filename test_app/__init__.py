# test_app package identifier
import logging

from django.conf import settings

from inbound_email.signals import email_received

logger = logging.getLogger(__name__)


def on_email_received(sender, **kwargs):
    """Example signal handler that just switches to/from addresses and resends."""
    request = kwargs.pop('request', None)
    email = kwargs.pop('email', None)
    logger.debug(
        u"Sending email from %s straight back to them: '%s'",
        email.from_email, email.subject
    )
    try:
        from_email = email.from_email
        email.from_email = email.to[0]
        email.to = [from_email]
        email.send()
    except:
        logger.exception(
            u"Something went wrong with the bounceback. See trace for details."
        )


if settings.BOUNCEBACK_ENABLED:
    logger.info(u"Email bounceback feature is enabled.")
    email_received.connect(on_email_received)
