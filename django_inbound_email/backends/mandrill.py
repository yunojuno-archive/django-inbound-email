# encoding=utf-8

import re
import json
import logging
import base64

from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django_inbound_email.backends import RequestParser
from django.utils.encoding import smart_bytes


from django_inbound_email.errors import (
    RequestParseError,
    AttachmentTooLargeError,
)

logger = logging.getLogger(__name__)


def _detect_base64(s):
    """Quite an ingenuous function to guess if a string is base64 encoded
    """
    return (len(s) % 4 == 0) and re.match('^[A-Za-z0-9+/]+[=]{0,2}$', s)


class MandrillRequestParser(RequestParser):
    """Mandrill request parser. """

    def _process_attachments(self, email, attachments):
        for key, attachment in attachments.iteritems():
            is_base64 = attachment.get('base64')
            name = attachment.get('name')
            mimetype = attachment.get('type')
            content = attachment.get('content', u"")

            if is_base64:
                content = base64.b64decode(content)
            # watchout: sometimes attachment contents are base64'd but mandrill doesn't set the flag
            elif _detect_base64(content):
                content = base64.b64decode(content)

            content = smart_bytes(content, strings_only=True)

            if len(content) > self.max_file_size:
                logger.debug(
                    u"File attachment %s is too large to process (%sB)",
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
                    u"Inbound request is missing or got an invalid value.: %s." % ex
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
