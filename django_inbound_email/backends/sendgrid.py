# sendgrid specific request parser.
import json
import logging

from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.encoding import smart_text

from django_inbound_email.backends import RequestParser
from django_inbound_email.errors import (
    RequestParseError,
    AttachmentTooLargeError,
)

logger = logging.getLogger(__name__)


def _decode_POST_value(request, field_name, default=None):
    """Helper to decode a request field into unicode based on charsets encoding.

    Args:
        request: the HttpRequest object.
        field_name: the field expected in the request.POST

    Kwargs:
        default: if passed in then field is optional and default is used if not
            found; if None, then assume field exists, which will raise an error
            if it does not.

    Returns: the contents of the string encoded using the related charset from
        the requests.POST['charsets'] dictionary (or 'utf-8' if none specified).
    """
    if default is None:
        value = request.POST[field_name]
    else:
        value = request.POST.get(field_name, default)

    # it's inefficient to load this each time it gets called, but we're
    # not anticipating incoming email being a performance bottleneck right now!
    charsets = json.loads(request.POST.get('charsets', "{}"))
    charset = charsets.get(field_name, 'utf-8')

    if charset.lower() != 'utf-8':
        logger.debug("Incoming email field '%s' has %s encoding.", field_name, charset)

    return smart_text(value, encoding=charset)


class SendGridRequestParser(RequestParser):
    """SendGrid request parser."""

    def parse(self, request):
        """Parse incoming request and return an email instance.

        Args:
            request: an HttpRequest object, containing the forwarded email, as
                per the SendGrid specification for inbound emails.

        Returns:
            an EmailMultiAlternatives instance, containing the parsed contents
                of the inbound email.

        TODO: non-UTF8 charset handling.
        TODO: handler headers.
        """
        assert isinstance(request, HttpRequest), "Invalid request type: %s" % type(request)

        try:
            subject = _decode_POST_value(request, 'subject')
            from_email = _decode_POST_value(request, 'from')
            to_email = _decode_POST_value(request, 'to').split(',')
            text = _decode_POST_value(request, 'text')
            html = _decode_POST_value(request, 'html', default='')
            cc = _decode_POST_value(request, 'cc', default='').split(',')
            bcc = _decode_POST_value(request, 'bcc', default='').split(',')

        except MultiValueDictKeyError as ex:
            raise RequestParseError(u"Inbound request is missing required value: %s." % ex)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=from_email,
            to=to_email,
            cc=cc,
            bcc=bcc,
        )
        if html is not None and len(html) > 0:
            email.attach_alternative(html, "text/html")

        # TODO: this won't cope with big files - should really read in in chunks
        for n, f in request.FILES.iteritems():
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
                email.attach(f.name, f.read(), f.content_type)

        return email
