# sendgrid specific request parser.
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest

from django_inbound_email.backends import RequestParser
from django_inbound_email.exceptions import EmailParseError


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

        TODO: the real, bulletproof implementation. Fields need cleaning, proper
                unicode handling etc.
        TODO: handle attachments.
        TODO: handler headers.
        """
        assert isinstance(request, HttpRequest), "Invalid request type: %s" % type(request)

        subject = request.POST.get('subject')
        from_email = request.POST.get('from')
        to_email = request.POST.get('to', u"").split(',')
        text = request.POST.get('text')
        html = request.POST.get('html', u"")
        cc = request.POST.get('cc', u"").split(',')
        bcc = request.POST.get('bcc', u"").split(',')

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

        return email
