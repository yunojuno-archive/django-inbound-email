# -*- coding: utf-8 -*-
# Mailgun specific request parser. See http://www.mailgun.com/inbound-routing
import logging

from django.utils import six
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.utils.datastructures import MultiValueDictKeyError

from django_inbound_email.backends import RequestParser
from django_inbound_email.errors import (
    RequestParseError,
    AttachmentTooLargeError,
)

logger = logging.getLogger(__name__)


class MailgunRequestParser(RequestParser):
    """Mailgun request parser."""

    def parse(self, request):
        """Parse incoming request and return an email instance.

        Mailgun does a lot of the heavy lifting at their end - requests
        come in from them UTF-8 encoded, and with the message reply and
        signature stripped out for you.

        Args:
            request: an HttpRequest object, containing the forwarded email, as
                per the SendGrid specification for inbound emails.

        Returns:
            an EmailMultiAlternatives instance, containing the parsed contents
                of the inbound email.
        """
        assert isinstance(request, HttpRequest), "Invalid request type: %s" % type(request)

        try:
            subject = request.POST.get('subject', '')
            text = u"%s\n\n%s" % (
                request.POST.get('stripped-text', ''),
                request.POST.get('stripped-signature', '')
            )
            html = request.POST.get('stripped-html')
            from_email = request.POST.get('sender')
            to_email = request.POST.get('recipient')
            if not to_email:
                raise AttributeError("recipient")
            to_email = to_email.split(',')
            cc = request.POST.get('cc', '')
            if cc:
                cc = cc.split(',')
            bcc = request.POST.get('bcc', '')
            if bcc:
                bcc = bcc.split(',')

            date = request.POST.get('date') or request.POST.get('Date', '')

        except MultiValueDictKeyError as ex:
            raise RequestParseError(
                u"Inbound request is missing required value: %s." % ex
            )

        except AttributeError as ex:
            raise RequestParseError(
                u"Inbound request is missing required value: %s." % ex
            )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=from_email,
            to=to_email,
            cc=cc,
            bcc=bcc,
        )
        if date:
            email.extra_headers['date'] = date
        if html is not None and len(html) > 0:
            email.attach_alternative(html, "text/html")

        # TODO: this won't cope with big files - should really read in in chunks
        for n, f in six.iteritems(request.FILES):
            if f.size > self.max_file_size:
                logger.debug(
                    u"File attachment %s is too large to process (%sB)",
                    f.name,
                    f.size
                )
                raise AttachmentTooLargeError(
                    email=email,
                    filename=f.name,
                    size=f.size
                )
            else:
                email.attach(n, f.read(), f.content_type)

        return email
