# package definition file for django_inbound_email.backends
from importlib import import_module

from django.conf import settings


def get_backend_class():
    """Return reference to the configured backed class."""
    # this will (intentionally) blow up if the setting does not exist
    assert hasattr(settings, 'INBOUND_EMAIL_PARSER')
    assert getattr(settings, 'INBOUND_EMAIL_PARSER') is not None

    package, klass = settings.INBOUND_EMAIL_PARSER.rsplit('.', 1)
    module = import_module(package)
    return getattr(module, klass)


def get_backend_instance():
    """Dynamically create an instance of the configured backend class."""
    backend = get_backend_class()
    return backend()


class RequestParser():
    """Abstract base class, to be implemented by service-specific classes."""

    @property
    def max_file_size(self):
        """The maximum file size to process as an attachment (default=10MB)."""
        return getattr(settings, 'INBOUND_EMAIL_ATTACHMENT_SIZE_MAX', 10000000)

    def parse(self, request):
        """Parse a request object into an EmailMultiAlternatives instance.

        This function is where the hard word gets done. The following fields are
        parsed from the request.POST dict:

        * from - the sender
        * to - the recipient list
        * cc - the cc list
        * html - the HTML version of the email
        * text - the text version of the email
        * subject - the subject line
        * attachments

        Inheriting classes should raise RequestParseError if the inbound request
        cannot be converted successfully.

        """
        raise NotImplementedError("Must be implemented by inheriting class.")
