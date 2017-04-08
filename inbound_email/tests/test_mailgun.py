# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from os import path

from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.utils.encoding import smart_bytes

from ..backends.mailgun import MailgunRequestParser
from ..compat import reverse
from ..errors import RequestParseError, AttachmentTooLargeError

from .test_files.mailgun_post import test_inbound_payload as mailgun_payload


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
        self.assertEqual(email.to, data.get('recipient', '').split(','))
        self.assertEqual(email.from_email, data.get('sender', ''))
        self.assertEqual(email.subject, data.get('subject', ''))
        self.assertEqual(email.body, "%s\n\n%s" % (
            data.get('stripped-text', ''),
            data.get('stripped-signature', '')
        ))
        self.assertEqual(email.cc, data.get('cc', '').split(','))
        self.assertEqual(email.bcc, data.get('bcc', '').split(','))
        if 'html' in data:
            self.assertEqual(len(email.alternatives), 1)
            self.assertEqual(email.alternatives[0][0], data.get('stripped-html', ''))

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
        attachment_2 = open(self.test_upload_png, 'rb').read()
        data['attachment-1'] = open(self.test_upload_txt, 'r')
        data['attachment-2'] = open(self.test_upload_png, 'rb')
        request = self.factory.post(self.url, data=data)
        email = self.parser.parse(request)

        self._assertEmailParsedCorrectly(email, data)

        # for each attachmen, check the contents match the input
        self.assertEqual(len(email.attachments), 2)

        # convert list of 3-tuples into dict so we can lookup by filename
        attachments = {k[0]: (k[1], k[2]) for k in email.attachments}
        self.assertEqual(smart_bytes(attachments['attachment-1'][0]), smart_bytes(attachment_1))
        self.assertEqual(attachments['attachment-1'][1], 'text/plain')
        self.assertEqual(attachments['attachment-2'][0], attachment_2)
        self.assertEqual(attachments['attachment-2'][1], 'image/jpeg')

    @override_settings(INBOUND_EMAIL_ATTACHMENT_SIZE_MAX=0)
    def test_attachments_max_size(self):
        """Test inbound email attachment max size limit."""
        # receive an email
        data = mailgun_payload
        open(self.test_upload_txt, 'rb').read()
        open(self.test_upload_png, 'rb').read()
        data['attachment-1'] = open(self.test_upload_txt, 'rb')
        data['attachment-2'] = open(self.test_upload_png, 'rb')
        request = self.factory.post(self.url, data=data)

        # should except
        with self.assertRaises(AttachmentTooLargeError):
            self.parser.parse(request),
