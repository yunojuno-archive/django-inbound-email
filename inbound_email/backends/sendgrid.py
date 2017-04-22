# sendgrid specific request parser.
import json
import logging

from email.utils import getaddresses

from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.encoding import smart_text

from ..backends import RequestParser
from ..errors import RequestParseError, AttachmentTooLargeError

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

    def _get_addresses(self, address_data, retain_name=False):
        """
        Takes RFC-compliant email addresses in both terse (email only)
        and verbose (name + email) forms and returns a list of
        email address strings

        (TODO: breaking change that returns a tuple of (name, email) per string)
        """
        if retain_name:
            raise NotImplementedError(
                "Not yet implemented, but will need client-code changes too"
            )

        # We trust than an email address contains an "@" after
        # email.utils.getaddresses has done the hard work. If we wanted
        # to we could use a regex to check for greater email validity

        # NB: getaddresses expects a list, so ensure we feed it appropriately
        if isinstance(address_data, str):
            if "[" not in address_data:
                # Definitely turn these into a list
                # NB: this is pretty assumptive, but still prob OK
                address_data = [address_data]

        output = [x[1] for x in getaddresses(address_data) if "@" in x[1]]
        return output

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
            # from_email should never be a list (unless we change our API)
            from_email = self._get_addresses([_decode_POST_value(request, 'from')])[0]

            # ...but all these can and will be a list
            to_email = self._get_addresses([_decode_POST_value(request, 'to')])
            cc = self._get_addresses([_decode_POST_value(request, 'cc', default='')])
            bcc = self._get_addresses([_decode_POST_value(request, 'bcc', default='')])

            subject = _decode_POST_value(request, 'subject')
            text = _decode_POST_value(request, 'text', default='')
            html = _decode_POST_value(request, 'html', default='')

        except IndexError as ex:
            raise RequestParseError(
                "Inbound request lacks a valid from address: %s." % request.get('from')
            )

        except MultiValueDictKeyError as ex:
            raise RequestParseError("Inbound request is missing required value: %s." % ex)

        if "@" not in from_email:
            # Light sanity check for potential issues related to taking just the
            # first element of the 'from' address list
            raise RequestParseError("Could not get a valid from address out of: %s." % request)

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
        for n, f in list(request.FILES.items()):
            if f.size > self.max_file_size:
                logger.debug(
                    "File attachment %s is too large to process (%sB)",
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
