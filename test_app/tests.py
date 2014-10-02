# -*- coding: utf-8 -*-
from os import path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.utils.encoding import smart_text

from django_inbound_email.backends import (
    get_backend_instance,
    RequestParseError,
    AttachmentTooLargeError
)
from django_inbound_email.backends.sendgrid import SendGridRequestParser
from django_inbound_email.backends.mailgun import MailgunRequestParser
from django_inbound_email.signals import email_received, email_received_unacceptable
from django_inbound_email.views import receive_inbound_email, _log_request

from test_app.test_files.sendgrid_post import test_inbound_payload as sendgrid_payload
from test_app.test_files.mailgun_post import test_inbound_payload as mailgun_payload
from test_app.test_files.sendgrid_post_windows_1252 import test_inbound_payload_1252

# don't read it out of the settings - fix it here so we know what we're using
DEFAULT_TEST_PARSER = "django_inbound_email.backends.sendgrid.SendGridRequestParser"


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
        self.parser = SendGridRequestParser()  # use a known entity for now.

        # need to have something here to pass the ViewFunctionTests
        settings.INBOUND_EMAIL_PARSER = DEFAULT_TEST_PARSER

        self.test_upload_txt = path.join(path.dirname(__file__), 'test_files/test_upload_file.txt')

    def test_log_inbound_requests(self):
        """Test the internal log function."""
        # just to exercise the function - it doesn't 'do' anything other than
        # log to the console, but is good to know that it doesn't break.
        request = self.factory.post(self.url, data=sendgrid_payload)
        _log_request(request)

    def test_valid_request(self):
        """Test the RequestParseErrors are handled correctly, and return HTTP 200."""
        request = self.factory.post(self.url, data=sendgrid_payload)
        response = receive_inbound_email(request)
        self.assertContains(response, u"Successfully parsed", status_code=200)

    def test_parse_error_response_200(self):
        """Test the RequestParseErrors are handled correctly, and return HTTP 200."""
        settings.INBOUND_EMAIL_RESPONSE_200 = True
        request = self.factory.post(self.url, data={})
        response = receive_inbound_email(request)
        self.assertContains(response, u"Unable to parse", status_code=200)

    def test_parse_error_response_400(self):
        """Test the RequestParseErrors are handled correctly, and return HTTP 400."""
        settings.INBOUND_EMAIL_RESPONSE_200 = False
        request = self.factory.post(self.url, data={})
        response = receive_inbound_email(request)
        self.assertContains(response, u"Unable to parse", status_code=400)

    def test_email_received_signal(self):
        """Test that a valid POST fires the email_received signal."""

        request = self.factory.post(self.url, data=sendgrid_payload)

        # define handler
        def on_email_received(sender, **kwargs):
            self.on_email_received_fired = True
            self.assertIsNone(sender)
            request = kwargs.pop('request', None)
            email = kwargs.pop('email', None)
            self.assertIsNotNone(email)
            self.assertIsInstance(email, EmailMultiAlternatives)
            self.assertIsNotNone(request)

        # connect handler
        email_received.connect(on_email_received)
        self.on_email_received_fired = False

        # fire a request in to force the signal to fire
        receive_inbound_email(request)
        self.assertTrue(self.on_email_received_fired)

    def test_email_received_unacceptable_signal_fired_for_too_large_attachment(self):
        # set a zero allowed max attachment size
        settings.INBOUND_EMAIL_ATTACHMENT_SIZE_MAX = 0

        # add attachment to payload
        data = sendgrid_payload
        data['attachment'] = open(self.test_upload_txt, 'r')

        request = self.factory.post(self.url, data=data)

        # define handler
        def on_email_received(sender, **kwargs):
            self.on_email_received_fired = True
            self.assertIsNone(sender)
            request = kwargs.pop('request', None)
            email = kwargs.pop('email', None)
            exception = kwargs.pop('exception', None)

            self.assertIsNotNone(request)
            self.assertIsInstance(email, EmailMultiAlternatives)
            self.assertIsInstance(exception, AttachmentTooLargeError)
            self.assertEqual(exception.filename, 'test_upload_file.txt')

        # connect handler
        email_received_unacceptable.connect(on_email_received)
        self.on_email_received_fired = False

        # fire a request in to force the signal to fire
        receive_inbound_email(request)
        self.assertTrue(self.on_email_received_fired)


class SendGridRequestParserTests(TestCase):
    """Tests for SendGridRequestParser - NB test use parser direct, not via view."""

    def _assertEmailParsedCorrectly(self, email, data):
        """Helper assert method that matches email properties to posted data.

        It's pulled out here as this is used in most of the tests to assert that
        the parser worked properly.

        Args:
            email: the EmailMultiAlternatives object to test.
            data: a dict of data that was sent to the parser.

        """
        self.assertIsInstance(email, EmailMultiAlternatives)
        self.assertEqual(email.to, data.get('to', u'').split(','))
        self.assertEqual(email.from_email, data.get('from', u''))
        self.assertEqual(email.subject, data.get('subject', u''))
        self.assertEqual(email.body, data.get('text', u''))
        self.assertEqual(email.cc, data.get('cc', u'').split(','))
        self.assertEqual(email.bcc, data.get('bcc', u'').split(','))
        if 'html' in data:
            self.assertEqual(len(email.alternatives), 1)
            self.assertEqual(email.alternatives[0][0], data.get('html', u''))

    def setUp(self):
        # Every test needs access to the request factory.
        self.url = reverse('receive_inbound_email')
        self.factory = RequestFactory()
        self.parser = SendGridRequestParser()
        self.test_upload_txt = path.join(path.dirname(__file__), 'test_files/test_upload_file.txt')
        self.test_upload_png = path.join(path.dirname(__file__), 'test_files/test_upload_file.jpg')

    def test_parse_valid_request(self):
        """Test that a valid POST returns a 200."""
        request = self.factory.post(self.url, data=sendgrid_payload)
        email = self.parser.parse(request)
        self._assertEmailParsedCorrectly(email, sendgrid_payload)

    def test_parse_invalid_request(self):
        """Test that an invalid request raises RequestParseError."""
        request = self.factory.post(self.url, data={})
        self.assertRaises(RequestParseError, self.parser.parse, request)

    def test_text_email_only(self):
        """Test inbound email with no HTML alternative."""
        data = sendgrid_payload
        del data['html']
        request = self.factory.post(self.url, data=data)
        email = self.parser.parse(request)
        self._assertEmailParsedCorrectly(email, sendgrid_payload)

    def test_attachments(self):
        """Test inbound email with attachments."""
        data = sendgrid_payload
        attachment_1 = open(self.test_upload_txt, 'r').read()
        attachment_2 = open(self.test_upload_png, 'r').read()
        data['attachment1'] = open(self.test_upload_txt, 'r')
        data['attachment2'] = open(self.test_upload_png, 'r')
        request = self.factory.post(self.url, data=data)
        email = self.parser.parse(request)

        self._assertEmailParsedCorrectly(email, data)

        # for each attachmen, check the contents match the input
        self.assertEqual(len(email.attachments), 2)

        # convert list of 3-tuples into dict so we can lookup by filename
        attachments = {k[0]: (k[1], k[2]) for k in email.attachments}
        self.assertEqual(attachments['attachment1'][0], attachment_1)
        self.assertEqual(attachments['attachment1'][1], 'text/plain')
        self.assertEqual(attachments['attachment2'][0], attachment_2)
        self.assertEqual(attachments['attachment2'][1], 'image/jpeg')

    @override_settings(INBOUND_EMAIL_ATTACHMENT_SIZE_MAX=0)
    def test_attachments_max_size(self):
        """Test inbound email attachment max size limit."""
        # receive an email
        data = sendgrid_payload
        open(self.test_upload_txt, 'r').read()
        open(self.test_upload_png, 'r').read()
        data['attachment1'] = open(self.test_upload_txt, 'r')
        data['attachment2'] = open(self.test_upload_png, 'r')
        request = self.factory.post(self.url, data=data)

        # should except
        with self.assertRaises(AttachmentTooLargeError):
            self.parser.parse(request),

    def test_encodings(self):
        """Test inbound email with non-UTF8 encoded fields."""
        data = test_inbound_payload_1252
        request = self.factory.post(self.url, data=data)
        email = self.parser.parse(request)
        self.assertEqual(email.body, smart_text(data['text']))


class MailgunRequestParserTests(TestCase):
    """Tests for MailRequestParser - NB test use parser direct, not via view."""

    def _assertEmailParsedCorrectly(self, email, data):
        """Helper assert method that matches email properties to posted data.

        It's pulled out here as this is used in most of the tests to assert that
        the parser worked properly.

        Args:
            email: the EmailMultiAlternatives object to test.
            data: a dict of data that was sent to the parser.

        """
        self.assertIsInstance(email, EmailMultiAlternatives)
        self.assertEqual(email.to, data.get('recipient', u'').split(','))
        self.assertEqual(email.from_email, data.get('sender', u''))
        self.assertEqual(email.subject, data.get('subject', u''))
        self.assertEqual(email.body, u"%s\n\n%s" % (
            data.get('stripped-text', u''),
            data.get('stripped-signature', u'')
        ))
        self.assertEqual(email.cc, data.get('cc', u'').split(','))
        self.assertEqual(email.bcc, data.get('bcc', u'').split(','))
        if 'html' in data:
            self.assertEqual(len(email.alternatives), 1)
            self.assertEqual(email.alternatives[0][0], data.get('stripped-html', u''))

    def setUp(self):
        # Every test needs access to the request factory.
        self.url = reverse('receive_inbound_email')
        self.factory = RequestFactory()
        self.parser = MailgunRequestParser()
        self.test_upload_txt = path.join(path.dirname(__file__), 'test_files/test_upload_file.txt')
        self.test_upload_png = path.join(path.dirname(__file__), 'test_files/test_upload_file.jpg')

    def test_parse_valid_request(self):
        """Test that a valid POST returns a 200."""
        request = self.factory.post(self.url, data=mailgun_payload)
        email = self.parser.parse(request)
        self._assertEmailParsedCorrectly(email, mailgun_payload)

    def test_parse_invalid_request(self):
        """Test that an invalid request raises RequestParseError."""
        request = self.factory.post(self.url, data={})
        self.assertRaises(RequestParseError, self.parser.parse, request)

    def test_text_email_only(self):
        """Test inbound email with no HTML alternative."""
        data = mailgun_payload
        del data['stripped-html']
        request = self.factory.post(self.url, data=data)
        email = self.parser.parse(request)
        self._assertEmailParsedCorrectly(email, mailgun_payload)

    def test_attachments(self):
        """Test inbound email with attachments."""
        data = mailgun_payload
        attachment_1 = open(self.test_upload_txt, 'r').read()
        attachment_2 = open(self.test_upload_png, 'r').read()
        data['attachment-1'] = open(self.test_upload_txt, 'r')
        data['attachment-2'] = open(self.test_upload_png, 'r')
        request = self.factory.post(self.url, data=data)
        email = self.parser.parse(request)

        self._assertEmailParsedCorrectly(email, data)

        # for each attachmen, check the contents match the input
        self.assertEqual(len(email.attachments), 2)

        # convert list of 3-tuples into dict so we can lookup by filename
        attachments = {k[0]: (k[1], k[2]) for k in email.attachments}
        self.assertEqual(attachments['attachment-1'][0], attachment_1)
        self.assertEqual(attachments['attachment-1'][1], 'text/plain')
        self.assertEqual(attachments['attachment-2'][0], attachment_2)
        self.assertEqual(attachments['attachment-2'][1], 'image/jpeg')

    @override_settings(INBOUND_EMAIL_ATTACHMENT_SIZE_MAX=0)
    def test_attachments_max_size(self):
        """Test inbound email attachment max size limit."""
        # receive an email
        data = mailgun_payload
        open(self.test_upload_txt, 'r').read()
        open(self.test_upload_png, 'r').read()
        data['attachment-1'] = open(self.test_upload_txt, 'r')
        data['attachment-2'] = open(self.test_upload_png, 'r')
        request = self.factory.post(self.url, data=data)

        # should except
        with self.assertRaises(AttachmentTooLargeError):
            self.parser.parse(request),
