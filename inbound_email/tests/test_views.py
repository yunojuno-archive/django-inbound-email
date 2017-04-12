# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os import path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from ..errors import (
    AttachmentTooLargeError,
    AuthenticationError,
)
from ..signals import email_received, email_received_unacceptable
from ..views import receive_inbound_email, _log_request

from .test_files.sendgrid_post import test_inbound_payload as sendgrid_payload
from .test_files.mailgun_post import test_inbound_payload as mailgun_payload
from .test_files.mandrill_post import post_data as mandrill_payload
from .test_files.mandrill_post import (
    post_data_with_attachments as mandrill_payload_with_attachments
)


# don't read it out of the settings - fix it here so we know what we're using
DEFAULT_TEST_PARSER = "inbound_email.backends.sendgrid.SendGridRequestParser"
MANDRILL_REQUEST_PARSER = "inbound_email.backends.mandrill.MandrillRequestParser"
SENDGRID_REQUEST_PARSER = "inbound_email.backends.sendgrid.SendGridRequestParser"
MAILGUN_REQUEST_PARSER = "inbound_email.backends.mailgun.MailgunRequestParser"


class ViewFunctionTests(TestCase):
    """Tests for the inbound view function receive_inbound_email.

    The view function is responsible for loading the correct backend, and
    firing the signal once the email is parsed. This test suite contains no
    parsing tests - these are covered in the relevant backend tests - just tests
    for the signals.

    """
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.url = reverse('receive_inbound_email')
        self.test_upload_txt = path.join(path.dirname(__file__), 'test_files/test_upload_file.txt')

    def _get_payloads_and_parsers(self, with_attachments=False):
        mpwa = mandrill_payload_with_attachments
        mp = mandrill_payload
        return [
            (MANDRILL_REQUEST_PARSER, mpwa if with_attachments else mp),
            (SENDGRID_REQUEST_PARSER, sendgrid_payload),
            (MAILGUN_REQUEST_PARSER, mailgun_payload),
        ]

    def test_log_inbound_requests(self):
        """Test the internal log function."""
        # just to exercise the function - it doesn't 'do' anything other than
        # log to the console, but is good to know that it doesn't break.

        for klass, payload in self._get_payloads_and_parsers():
            settings.INBOUND_EMAIL_PARSER = klass
            request = self.factory.post(self.url, data=payload)
            _log_request(request)

    def test_inbound_request_HEAD_200(self):
        """Return 200 OK to a HEAD request."""
        request = self.factory.head(self.url)
        response = receive_inbound_email(request)
        self.assertEqual(response.status_code, 200)

    def test_valid_request(self):
        """Test the RequestParseErrors are handled correctly, and return HTTP 200."""
        for klass, payload in self._get_payloads_and_parsers():
            settings.INBOUND_EMAIL_PARSER = klass
            request = self.factory.post(self.url, data=payload)
            response = receive_inbound_email(request)
            self.assertContains(response, "Successfully parsed", status_code=200)

    def test_parse_error_response_200(self):
        """Test the RequestParseErrors are handled correctly, and return HTTP 200."""
        settings.INBOUND_EMAIL_RESPONSE_200 = True
        for klass, payload in self._get_payloads_and_parsers():
            settings.INBOUND_EMAIL_PARSER = klass
            request = self.factory.post(self.url, data={})
            response = receive_inbound_email(request)
            self.assertContains(response, "Unable to parse", status_code=200)

    def test_parse_error_response_400(self):
        """Test the RequestParseErrors are handled correctly, and return HTTP 400."""
        settings.INBOUND_EMAIL_RESPONSE_200 = False
        request = self.factory.post(self.url, data={})
        response = receive_inbound_email(request)
        self.assertContains(response, "Unable to parse", status_code=400)

    def test_email_received_signal(self):
        """Test that a valid POST fires the email_received signal."""
        # define handler
        for klass, payload in self._get_payloads_and_parsers():

            def on_email_received(sender, **kwargs):
                self.on_email_received_fired = True
                self.assertEqual(sender.__name__, klass.split('.')[-1])
                request = kwargs.pop('request', None)
                email = kwargs.pop('email', None)
                self.assertIsNotNone(email)
                self.assertIsInstance(email, EmailMultiAlternatives)
                self.assertIsNotNone(request)
            email_received.connect(on_email_received)

            settings.INBOUND_EMAIL_PARSER = klass
            request = self.factory.post(self.url, data=payload)

            # connect handler
            self.on_email_received_fired = False

            # fire a request in to force the signal to fire
            receive_inbound_email(request)
            self.assertTrue(self.on_email_received_fired)

            email_received.disconnect(on_email_received)

    def test_email_received_unacceptable_signal_fired_for_too_large_attachment(self):
        # set a zero allowed max attachment size
        settings.INBOUND_EMAIL_ATTACHMENT_SIZE_MAX = 0

        for klass, payload in self._get_payloads_and_parsers(with_attachments=True):
            settings.INBOUND_EMAIL_PARSER = klass
            _payload = payload.copy()

            if klass == SENDGRID_REQUEST_PARSER:
                _payload['attachment'] = open(self.test_upload_txt, 'r')
            if klass == MAILGUN_REQUEST_PARSER:
                _payload['attachment-1'] = open(self.test_upload_txt, 'r')

            # define handler
            def on_email_received(sender, **kwargs):
                self.on_email_received_fired = True
                request = kwargs.pop('request', None)
                email = kwargs.pop('email', None)
                exception = kwargs.pop('exception', None)
                self.assertEqual(sender.__name__, klass.split('.')[-1])
                self.assertIsNotNone(request)
                self.assertIsInstance(email, EmailMultiAlternatives)
                self.assertIsInstance(exception, AttachmentTooLargeError)
            email_received_unacceptable.connect(on_email_received)

            self.on_email_received_fired = False

            request = self.factory.post(self.url, data=_payload)
            receive_inbound_email(request)
            self.assertTrue(self.on_email_received_fired, klass)
            email_received_unacceptable.disconnect(on_email_received)

    @override_settings(INBOUND_MANDRILL_AUTHENTICATION_KEY='mandrill_key')
    def test_email_received_unacceptable_signal_fired_for_mandrill_mistmatch_signature(self):
        parser = MANDRILL_REQUEST_PARSER
        payload = mandrill_payload
        settings.INBOUND_EMAIL_PARSER = parser
        _payload = payload.copy()

        # define handler
        def on_email_received(sender, **kwargs):
            self.on_email_received_fired = True
            request = kwargs.pop('request', None)
            email = kwargs.pop('email', None)
            exception = kwargs.pop('exception', None)
            self.assertEqual(sender.__name__, parser.split('.')[-1])
            self.assertIsNotNone(request)
            self.assertIsNone(email,)
            self.assertIsInstance(exception, AuthenticationError)
        email_received_unacceptable.connect(on_email_received)

        self.on_email_received_fired = False

        request = self.factory.post(
            self.url,
            data=_payload,
            HTTP_X_MANDRILL_SIGNATURE='invalid_signature',
        )
        receive_inbound_email(request)
        self.assertTrue(self.on_email_received_fired, parser)
        email_received_unacceptable.disconnect(on_email_received)
