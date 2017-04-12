# encoding=utf-8
from __future__ import unicode_literals

import re
import hashlib
import hmac
import json
import logging
import base64

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.utils.encoding import smart_bytes

from ..backends import RequestParser
from ..errors import (
    RequestParseError,
    AttachmentTooLargeError,
    AuthenticationError,
)

logger = logging.getLogger(__name__)


class MandrillSignatureMismatchError(AuthenticationError):
    """Error raised when the request's mandrill signature doesn't match.
    """

    def __init__(self, request, expected, calculated):
        super(MandrillSignatureMismatchError, self)
        self.request = request
        self.expected_signature = expected
        self.calculated_signature = calculated


def _detect_base64(s):
    """Quite an ingenuous function to guess if a string is base64 encoded
    """
    return (len(s) % 4 == 0) and re.match('^[A-Za-z0-9+/]+[=]{0,2}$', s)


def _check_mandrill_signature(request, key):
    expected = request.META.get('HTTP_X_MANDRILL_SIGNATURE', None)
    url = request.build_absolute_uri()
    # Mandrill appends the POST params in alphabetical order of the key.
    params = sorted(request.POST.items(), key=lambda x: x[0])
    message = url + ''.join(key + value for key, value in params)
    signed_binary = hmac.new(
        key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha1,
    )
    signature = base64.b64encode(signed_binary.digest()).decode('utf-8')
    if signature != expected:
        raise MandrillSignatureMismatchError(request, expected, signature)


class MandrillRequestParser(RequestParser):
    """Mandrill request parser. """

    def _process_attachments(self, email, attachments):
        for key, attachment in list(attachments.items()):
            is_base64 = attachment.get('base64')
            name = attachment.get('name')
            mimetype = attachment.get('type')
            content = attachment.get('content', "")

            if is_base64:
                content = base64.b64decode(content)
            # watchout: sometimes attachment contents are base64'd but mandrill doesn't set the flag
            elif _detect_base64(content):
                content = base64.b64decode(content)

            content = smart_bytes(content, strings_only=True)

            if len(content) > self.max_file_size:
                logger.debug(
                    "File attachment %s is too large to process (%sB)",
                    name,
                    len(content)
                )
                raise AttachmentTooLargeError(
                    email=email,
                    filename=name,
                    size=len(content)
                )

            if name and mimetype and content:
                email.attach(name, content, mimetype)
        return email

    def _get_recipients(self, array):
        """Returns an iterator of objects
           in the form ["Name <address@example.com", ...]
           from the array [["address@example.com", "Name"]]
        """
        for address, name in array:
            if not name:
                yield address
            else:
                yield "\"%s\" <%s>" % (name, address)

    def _get_sender(self, from_email, from_name=None):
        if not from_name:
            return from_email
        else:
            return "\"%s\" <%s>" % (from_name, from_email)

    def parse(self, request):
        """Parse incoming request and return an email instance.

        Args:
            request: an HttpRequest object, containing a list of forwarded emails, as
                per Mandrill specification for inbound emails.

        Returns:
            a list of EmailMultiAlternatives instances
        """
        assert isinstance(request, HttpRequest), "Invalid request type: %s" % type(request)

        if settings.INBOUND_MANDRILL_AUTHENTICATION_KEY:
            _check_mandrill_signature(
                request=request,
                key=settings.INBOUND_MANDRILL_AUTHENTICATION_KEY,
            )

        try:
            messages = json.loads(request.POST['mandrill_events'])
        except (ValueError, KeyError) as ex:
            raise RequestParseError("Request is not a valid json: %s" % ex)

        if not messages:
            logger.debug("No messages found in mandrill request: %s", request.body)
            return []

        emails = []
        for message in messages:
            if message.get('event') != 'inbound':
                logger.debug("Discarding non-inbound message")
                continue

            msg = message.get('msg')
            try:
                from_email = msg['from_email']
                to = list(self._get_recipients(msg['to']))

                subject = msg.get('subject', "")

                attachments = msg.get('attachments', {})
                attachments.update(msg.get('images', {}))

                text = msg.get('text', "")
                html = msg.get('html', "")
            except (KeyError, ValueError) as ex:
                raise RequestParseError(
                    "Inbound request is missing or got an invalid value.: %s." % ex
                )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email=self._get_sender(
                    from_email=from_email,
                    from_name=msg.get('from_name'),
                ),
                to=to,
            )
            if html is not None and len(html) > 0:
                email.attach_alternative(html, "text/html")

            email = self._process_attachments(email, attachments)
            emails.append(email)

        return emails
