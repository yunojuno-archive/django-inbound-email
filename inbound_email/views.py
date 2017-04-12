# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .backends import get_backend_instance
from .errors import (
    RequestParseError,
    AttachmentTooLargeError,
    AuthenticationError,
)
from .signals import email_received, email_received_unacceptable


logger = logging.getLogger(__name__)
log_requests = getattr(settings, 'INBOUND_EMAIL_LOG_REQUESTS', False)


def _log_request(request):
    """Helper function to dump out debug info."""
    logger.debug("Inbound email received")

    for k, v in list(request.POST.items()):
        logger.debug("- POST['%s']='%s'" % (k, v))

    for n, f in list(request.FILES.items()):
        logger.debug("- FILES['%s']: '%s', %sB", n, f.content_type, f.size)


@require_http_methods(["HEAD", "POST"])
@csrf_exempt
def receive_inbound_email(request):
    """Receives inbound email from SendGrid.

    This view receives the email from SendGrid, parses the contents, logs
    the message and the fires the inbound_email signal.

    """
    # log the request.POST and request.FILES contents
    if log_requests is True:
        _log_request(request)

    # HEAD requests are used by some backends to validate the route
    if request.method == 'HEAD':
        return HttpResponse('OK')

    try:
        # clean up encodings and extract relevant fields from request.POST
        backend = get_backend_instance()
        emails = backend.parse(request)

        # backend.parse can return either an EmailMultiAlternatives
        # or a list of those
        if emails:
            if isinstance(emails, EmailMultiAlternatives):
                emails = [emails]
            for email in emails:
                # fire the signal for each email
                email_received.send(sender=backend.__class__, email=email, request=request)

    except AttachmentTooLargeError as ex:
        logger.exception(ex)
        email_received_unacceptable.send(
            sender=backend.__class__,
            email=ex.email,
            request=request,
            exception=ex
        )
    except AuthenticationError as ex:
        logger.exception(ex)
        email_received_unacceptable.send(
            sender=backend.__class__,
            email=None,
            request=request,
            exception=ex
        )

    except RequestParseError as ex:
        logger.exception(ex)
        if getattr(settings, 'INBOUND_EMAIL_RESPONSE_200', True):
            # NB even if we have a problem, always use HTTP_STATUS=200, as
            # otherwise the email service will continue polling us with the email.
            # This is the default behaviour.
            status_code = 200
        else:
            status_code = 400

        return HttpResponse(
            "Unable to parse inbound email: %s" % ex,
            status=status_code
        )

    return HttpResponse("Successfully parsed inbound email.", status=200)
