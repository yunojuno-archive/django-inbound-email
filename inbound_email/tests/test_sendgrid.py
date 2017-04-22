# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os import path

from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.utils.encoding import smart_text, smart_bytes

from ..backends.sendgrid import SendGridRequestParser
from ..compat import reverse
from ..errors import RequestParseError, AttachmentTooLargeError

from .test_files.sendgrid_post import test_inbound_payload as sendgrid_payload
from .test_files.sendgrid_post_windows_1252 import test_inbound_payload_1252


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
                [data.get('to', '')]
            )
        )
        self.assertEqual(
            email.from_email,  # NB: This should/will not be a list...
            self.parser._get_addresses(
                data.get('from', '')
            )[0],  # ...so we don't want a list from _get_addresses either
        )
        self.assertEqual(email.subject, data.get('subject', ''))
        self.assertEqual(email.body, data.get('text', ''))
        self.assertEqual(
            email.cc,
            self.parser._get_addresses(
                [data.get('cc', '')]
            )
        )
        self.assertEqual(
            email.bcc,
            self.parser._get_addresses(
                [data.get('bcc', '')]
            )
        )
        if 'html' in data:
            self.assertEqual(len(email.alternatives), 1)
            self.assertEqual(email.alternatives[0][0], data.get('html', ''))

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
                {"bcc": '"Bartlet, Jed" <jed@whitehouse.gov>, "Zeigler, Toby" <toby@whitehouse.gov'},  # noqa
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
                # Latin 1 example
                {"to": '"McTøst, Sīla" <sīla@exañple.com>'},
                "to",
                ['sīla@exañple.com'],
            ),
            (
                # real-world edge case example
                {"to": """"Polo, Marco" <Marco.Polo@example.com>, "Koti, Shareen" <Shareen.Koti@example.com>, Rudi Cant-Fail <X18@messages.yunojuno.com>"""},  # noqa
                "to",
                ['Marco.Polo@example.com', 'Shareen.Koti@example.com', 'X18@messages.yunojuno.com'],  # noqa
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

    def test_text_html_only(self):
        """Test inbound email with no text body."""
        data = sendgrid_payload
        del data['text']
        request = self.factory.post(self.url, data=data)
        email = self.parser.parse(request)
        self._assertEmailParsedCorrectly(email, sendgrid_payload)

    def test_attachments(self):
        """Test inbound email with attachments."""
        data = sendgrid_payload
        attachment_1 = open(self.test_upload_txt, 'r').read()
        attachment_2 = open(self.test_upload_png, 'rb').read()
        data['attachment1'] = open(self.test_upload_txt, 'r')
        data['attachment2'] = open(self.test_upload_png, 'rb')
        request = self.factory.post(self.url, data=data)
        email = self.parser.parse(request)

        self._assertEmailParsedCorrectly(email, data)

        # for each attachmen, check the contents match the input
        self.assertEqual(len(email.attachments), 2)

        # convert list of 3-tuples into dict so we can lookup by filename
        attachments = {k[0]: (k[1], k[2]) for k in email.attachments}
        self.assertEqual(smart_bytes(attachments['test_upload_file.txt'][0]), smart_bytes(attachment_1))
        self.assertEqual(attachments['test_upload_file.txt'][1], 'text/plain')
        self.assertEqual(attachments['test_upload_file.jpg'][0], attachment_2)
        self.assertEqual(attachments['test_upload_file.jpg'][1], 'image/jpeg')

    @override_settings(INBOUND_EMAIL_ATTACHMENT_SIZE_MAX=0)
    def test_attachments_max_size(self):
        """Test inbound email attachment max size limit."""
        # receive an email
        data = sendgrid_payload
        open(self.test_upload_txt, 'r').read()
        open(self.test_upload_png, 'rb').read()
        data['attachment1'] = open(self.test_upload_txt, 'r')
        data['attachment2'] = open(self.test_upload_png, 'rb')
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
