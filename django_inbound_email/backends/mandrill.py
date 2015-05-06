import json
import logging

from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django_inbound_email.backends import RequestParser

from django_inbound_email.errors import (
    RequestParseError,
    AttachmentTooLargeError,
)

logger = logging.getLogger(__name__)


class MandrillRequestParser(RequestParser):
    """Mandrill request parser. """

    def _process_attachments(self, email, attachments):
        for key, attachment in attachments.iteritems():
            name = attachment.get('name')
            mimetype = attachment.get('type')
            content = attachment.get('content')

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
                from_name = msg['from_name']

                to = msg['to']
                subject = msg['subject']

                attachments = msg.get('attachments', {})
                attachments.update(msg.get('images', {}))

                text = msg['text']
                html = msg.get('html')
            except KeyError as ex:
                raise RequestParseError(
                    u"Inbound request is missing required value: %s." % ex
                )

            email = EmailMultiAlternatives(
                subject=subject,
                body=text,
                from_email="%s <%s>" % (from_name, from_email),
                to=to
            )
            if html is not None and len(html) > 0:
                email.attach_alternative(html, "text/html")

            email = self._process_attachments(email, attachments)
            emails.append(email)

        return emails
