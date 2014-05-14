# sendgrid specific request parser.
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.utils.datastructures import MultiValueDictKeyError

from django_inbound_email.backends import RequestParser, RequestParseError


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
            subject = request.POST['subject']
            from_email = request.POST['from']
            to_email = request.POST['to'].split(',')
            text = request.POST.get('text', u'')
            html = request.POST.get('html', u'')
            cc = request.POST.get('cc', u'').split(',')
            bcc = request.POST.get('bcc', u'').split(',')

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
            email.attach(n, f.read(), f.content_type)

        return email
