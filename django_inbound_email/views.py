# View functions for django-inbound-email
# -*- coding: utf-8 -*-
from importlib import import_module
import json
import logging

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, HttpResponse

from django_inbound_email.signals import email_received
from django_inbound_email.backends import get_backend_instance

logger = logging.getLogger(__name__)
backend = get_backend_instance()
log_requests = getattr(settings, 'LOG_INBOUND_EMAIL_REQUESTS', False)


def _log_inbound_email(request):
    """Helper function to dump out debug info."""
    logger.debug("Inbound email received:")

    for k, v in request.POST.iteritems():
        logger.debug("- POST['%s']='%s'" % (k, v))

    for n, f in request.FILES.iteritems():
        logger.debug("- FILES['%s']: '%s', %sB", n, f.content_type, f.size)


def _validate_request_fields(request, fields):
    """Helper function to validate that certain fields exist.

    Args:
        request: the HttpRequest object to test.
        fields: a list of field names to look for in the request.POST.

    Returns:
        bool, True if all the fields exist, else False.
    """
    for f in fields:
        if f not in request.POST:
            return False
    return True


@require_POST
@csrf_exempt
def receive_inbound_email(request):
    """Receives inbound email from SendGrid.

    This view receives the email from SendGrid, parses the contents, logs
    the message and the fires the inbound_email signal.

    TODO: add support for attachments
    TODO: add support for multiple backends
    """
    # log the request.POST and request.FILES contents
    if log_requests is True:
        _log_inbound_email(request)

    if not _validate_request_fields(request, ['to', 'from', 'subject']):
        # NB even if we have a problem, always use HTTP_STATUS=200, as
        # otherwise the email service will continue polling us with the email.
        return HttpResponse(u"Unable to parse inbound email.", status=200)

    # clean up encodings and extract relevant fields from request.POST
    email = backend.parse(request)

    # fire the signal
    email_received.send(sender=None, email=email, request=request)

    return HttpResponse(u"Successfully parsed inbound email.")
