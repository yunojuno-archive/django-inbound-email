# -*- coding: utf-8 -*-
from os import path
import json

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.utils.encoding import smart_text

from django_inbound_email.errors import (
    RequestParseError,
    AttachmentTooLargeError
)
from django_inbound_email.backends.sendgrid import SendGridRequestParser
from django_inbound_email.backends.mailgun import MailgunRequestParser
from django_inbound_email.backends.mandrill import MandrillRequestParser
from django_inbound_email.signals import email_received, email_received_unacceptable
from django_inbound_email.views import receive_inbound_email, _log_request

from test_app.test_files.sendgrid_post import test_inbound_payload as sendgrid_payload
from test_app.test_files.mailgun_post import test_inbound_payload as mailgun_payload
from test_app.test_files.sendgrid_post_windows_1252 import test_inbound_payload_1252
from test_app.test_files.mandrill_post import post_data as mandrill_payload


# don't read it out of the settings - fix it here so we know what we're using
DEFAULT_TEST_PARSER = "django_inbound_email.backends.sendgrid.SendGridRequestParser"
MANDRILL_REQUEST_PARSER = "django_inbound_email.backends.mandrill.MandrillRequestParser"
SENDGRID_REQUEST_PARSER = "django_inbound_email.backends.sendgrid.SendGridRequestParser"
MAILGUN_REQUEST_PARSER = "django_inbound_email.backends.mailgun.MailgunRequestParser"


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

    def _get_payloads_and_parsers(self):
        return [
            (MANDRILL_REQUEST_PARSER, mandrill_payload),
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

    def test_valid_request(self):
        """Test the RequestParseErrors are handled correctly, and return HTTP 200."""
        for klass, payload in self._get_payloads_and_parsers():
            settings.INBOUND_EMAIL_PARSER = klass
            request = self.factory.post(self.url, data=payload)
            response = receive_inbound_email(request)
            self.assertContains(response, u"Successfully parsed", status_code=200)

    def test_parse_error_response_200(self):
        """Test the RequestParseErrors are handled correctly, and return HTTP 200."""
        settings.INBOUND_EMAIL_RESPONSE_200 = True
        for klass, payload in self._get_payloads_and_parsers():
            settings.INBOUND_EMAIL_PARSER = klass
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

        for klass, payload in self._get_payloads_and_parsers():
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
        self.parser = SendGridRequestParser()

        self.assertIsInstance(email, EmailMultiAlternatives)
        self.assertEqual(
            email.to,
            self.parser._get_addresses(
                [data.get('to', u'')]
            )
        )
        self.assertEqual(
            email.from_email,  # NB: This should/will not be a list...
            self.parser._get_addresses(
                data.get('from', u'')
            )[0],  # ...so we don't want a list from _get_addresses either
        )
        self.assertEqual(email.subject, data.get('subject', u''))
        self.assertEqual(email.body, data.get('text', u''))
        self.assertEqual(
            email.cc,
            self.parser._get_addresses(
                [data.get('cc', u'')]
            )
        )
        self.assertEqual(
            email.bcc,
            self.parser._get_addresses(
                [data.get('bcc', u'')]
            )
        )
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

    def test_recipient_field_parsing(self):
        for payload_changes, attr_name, expected in [
            # TO
            (
                {"to": 'jed@whitehouse.gov'},
                "to",
                ['jed@whitehouse.gov'],
            ),
            (
                {"to": 'jed@whitehouse.gov, toby@whitehouse.gov'},
                "to",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),
            (
                {"to": '"Bartlet, Jed" <jed@whitehouse.gov>'},
                "to",
                ['jed@whitehouse.gov'],
            ),
            (
                {"to": 'Jed Bartlet <jed@whitehouse.gov>'},
                "to",
                ['jed@whitehouse.gov'],
            ),
            (
                {"to": '"Bartlet, Jed" <jed@whitehouse.gov>, "Zeigler, Toby" <toby@whitehouse.gov'},
                "to",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),
            (
                {"to": 'Jed Bartlet <jed@whitehouse.gov>, Toby Ziegler <toby@whitehouse.gov'},
                "to",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),
            (
                {"to": 'jed@whitehouse.gov, toby@whitehouse.gov'},
                "to",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),

            # FROM
            # NB: we do not get back a list
            (
                {"from": 'jed@whitehouse.gov'},
                "from_email",
                'jed@whitehouse.gov',
            ),
            (
                {"from": 'Jed Bartlet <jed@whitehouse.gov>'},
                "from_email",
                'jed@whitehouse.gov',
            ),
            (
                {"from": '"Bartlet, Jed" <jed@whitehouse.gov>'},
                "from_email",
                'jed@whitehouse.gov',
            ),

            # CC
            (
                {"cc": 'jed@whitehouse.gov'},
                "cc",
                ['jed@whitehouse.gov'],
            ),
            (
                {"cc": 'jed@whitehouse.gov, toby@whitehouse.gov'},
                "cc",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),
            (
                {"cc": '"Bartlet, Jed" <jed@whitehouse.gov>'},
                "cc",
                ['jed@whitehouse.gov'],
            ),
            (
                {"cc": '"Bartlet, Jed" <jed@whitehouse.gov>, "Zeigler, Toby" <toby@whitehouse.gov'},
                "cc",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),
            (
                {"cc": 'jed@whitehouse.gov, toby@whitehouse.gov'},
                "cc",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),

            # BCC
            (
                {"bcc": 'jed@whitehouse.gov'},
                "bcc",
                ['jed@whitehouse.gov'],
            ),
            (
                {"bcc": 'jed@whitehouse.gov, toby@whitehouse.gov'},
                "bcc",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),
            (
                {"bcc": '"Bartlet, Jed" <jed@whitehouse.gov>'},
                "bcc",
                ['jed@whitehouse.gov'],
            ),
            (
                {"bcc": '"Bartlet, Jed" <jed@whitehouse.gov>, "Zeigler, Toby" <toby@whitehouse.gov'},
                "bcc",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),
            (
                {"bcc": 'jed@whitehouse.gov, toby@whitehouse.gov'},
                "bcc",
                ['jed@whitehouse.gov', 'toby@whitehouse.gov'],
            ),
            # Handling edge-case or invalid content
            (
                # comma-separated names should be in double quotes
                {"to": 'Bartlet, Jed <jed@whitehouse.gov>'},
                "to",
                ['jed@whitehouse.gov'],
            ),
            (
                # extreme unicode
                {"to": u'"McTøst, Sīla" <sīla@exañple.come>'},
                "to",
                [u'sīla@exañple.come'],
            ),
            (
                # real-world edge case example
                {"to": u""""Djapri, Mario" <Mario.Djapri@lr.org>, "Kamakoti, Naveen" <Naveen.Kamakoti@lr.org>, Rudi Sellers <D1855@messages.yunojuno.com>"""},
                "to",
                [u'Mario.Djapri@lr.org', 'Naveen.Kamakoti@lr.org', 'D1855@messages.yunojuno.com'],
            )
        ]:

            payload = sendgrid_payload.copy()
            payload.update(payload_changes)

            request = self.factory.post(self.url, data=payload)
            email = self.parser.parse(request)

            self.assertEqual(
                getattr(email, attr_name),
                expected,
                "Failed to get %s for '%s' %s" % (
                    expected, attr_name, payload_changes
                )
            )

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
        self.assertEqual(attachments['test_upload_file.txt'][0], attachment_1)
        self.assertEqual(attachments['test_upload_file.txt'][1], 'text/plain')
        self.assertEqual(attachments['test_upload_file.jpg'][0], attachment_2)
        self.assertEqual(attachments['test_upload_file.jpg'][1], 'image/jpeg')

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


class MandrillRequestParserTests(TestCase):
    def setUp(self):
        self.url = reverse('receive_inbound_email')
        self.factory = RequestFactory()
        self.parser = MandrillRequestParser()
        self.payload = mandrill_payload

    def _assertEmailParsedCorrectly(self, emails, mandrill_payload, has_html=True):
        for i, e in enumerate(emails):
            msg = json.loads(mandrill_payload['mandrill_events'])[i]['msg']
            self.assertEqual(e.subject, msg['subject'])
            self.assertEqual(e.to, msg['to'])
            self.assertEqual(e.from_email, "%(from_name)s <%(from_email)s>" % msg)
            if has_html:
                self.assertEqual(e.alternatives[0][0], msg['html'])
            for name, contents, mimetype in e.attachments:
                self.assertEqual(msg['attachments'][name]['content'], contents)
                self.assertEqual(msg['attachments'][name]['type'], mimetype)
            self.assertEqual(e.body, msg['text'])

    def test_parse_valid_request(self):
        """
        Test a valid POST returns 200 and email(s) are correctly parsed
        """
        request = self.factory.post(self.url, data=mandrill_payload)
        emails = self.parser.parse(request)
        self._assertEmailParsedCorrectly(emails, mandrill_payload)

    def _process_dump(self, foo):
        dump = json.loads(self.payload['mandrill_events'])
        foo(dump)
        return json.dumps(dump)

    def test_parse_invalid_request(self):
        """Test that an invalid request raises RequestParseError."""
        _process = lambda dump: dump[0]['msg'].pop('text', None)

        payload = {'mandrill_events': self._process_dump(_process)}
        request = self.factory.post(self.url, data=payload)
        self.assertRaises(RequestParseError, self.parser.parse, request)

    def test_text_email_only(self):
        """Test inbound email with no HTML alternative."""
        _process = lambda dump: dump[0]['msg'].pop('html')

        payload = {'mandrill_events': self._process_dump(_process)}
        request = self.factory.post(self.url, data=payload)
        email = self.parser.parse(request)
        self._assertEmailParsedCorrectly(email, payload, has_html=False)

    @override_settings(INBOUND_EMAIL_ATTACHMENT_SIZE_MAX=0)
    def test_attachments_max_size(self):
        """Test inbound email attachment max size limit."""
        # receive an email
        request = self.factory.post(self.url, data=self.payload)
        # should except
        with self.assertRaises(AttachmentTooLargeError):
            self.parser.parse(request)
