# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import hmac
import json
import base64

from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.utils.encoding import smart_bytes

from ..backends.mandrill import (
    MandrillRequestParser,
    MandrillSignatureMismatchError,
)
from ..compat import reverse
from ..errors import RequestParseError, AttachmentTooLargeError

from .test_files.mandrill_post import post_data as mandrill_payload
from .test_files.mandrill_post import (
    post_data_with_attachments as mandrill_payload_with_attachments
)
from .test_files.mandrill_post import (
    post_data_with_attachments_mailbox as mandrill_payload_with_attachments_mailbox
)
from .test_files.mandrill_post import (
    post_data_with_attachments_mailbox_2 as mandrill_payload_with_attachments_mailbox_2
)


class MandrillRequestParserTests(TestCase):
    def setUp(self):
        self.url = reverse('receive_inbound_email')
        self.factory = RequestFactory()
        self.parser = MandrillRequestParser()
        self.payload = mandrill_payload
        self.payload_with_attachments = mandrill_payload_with_attachments

    def _assertEmailParsedCorrectly(self, emails, mandrill_payload, has_html=True):
        def _parse_to(to):
            ret = []
            for address, name in to:
                if not name:
                    ret.append(address)
                else:
                    ret.append("\"%s\" <%s>" % (name, address))
            return ret

        def _parse_from(name, email):
            if not name:
                return email
            return "\"%s\" <%s>" % (name, email)

        for i, e in enumerate(emails):
            msg = json.loads(mandrill_payload['mandrill_events'])[i]['msg']
            self.assertEqual(e.subject, msg['subject'])
            self.assertEqual(e.to, _parse_to(msg['to']))
            self.assertEqual(
                e.from_email,
                _parse_from(msg.get('from_name'), msg.get('from_email'))
            )
            if has_html:
                self.assertEqual(e.alternatives[0][0], msg['html'])
            for name, contents, mimetype in e.attachments:
                # Check that base64 contents are decoded
                is_base64 = msg['attachments'][name].get('base64')
                req_contents = msg['attachments'][name]['content']
                if is_base64:
                    req_contents = base64.b64decode(req_contents)
                self.assertEqual(smart_bytes(req_contents), smart_bytes(contents))
                self.assertEqual(msg['attachments'][name]['type'], mimetype)
            self.assertEqual(e.body, msg['text'])

    def _calculate_signature(self, url, data, key):
        # Mandrill appends the POST params in alphabetical order of the key.
        params = sorted(data, key=lambda x: x[0])
        message = url + ''.join(key + value for key, value in params)
        signed_binary = hmac.new(
            key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha1,
        )
        signature = base64.b64encode(signed_binary.digest())
        return signature.decode('utf-8')

    def test_parse_valid_request__with_attachments__from_mailbox(self):
        "Test email sent via Mailbox app without body text "
        request = self.factory.post(self.url, data=mandrill_payload_with_attachments_mailbox)
        emails = self.parser.parse(request)
        email = emails[0]
        payload = json.loads(mandrill_payload_with_attachments_mailbox['mandrill_events'])

        self.assertEqual(len(email.attachments), 1)
        self.assertEqual(email.attachments[0][0], '3c8e4ffb-6366-4351-813f-d0f600ed720e')
        self.assertEqual(email.attachments[0][2], 'image/jpeg')
        self.assertEqual(
            email.attachments[0][1],
            # the content is base64-decoded, even if the base64 flag is off in the request
            base64.b64decode(
                payload[0]['msg']['images']
                ['3c8e4ffb-6366-4351-813f-d0f600ed720e']['content']
            )
        )

    def test_parse_valid_request__with_attachments__from_mailbox__2(self):
        "Test email sent via Mailbox app with text "
        request = self.factory.post(self.url, data=mandrill_payload_with_attachments_mailbox_2)
        emails = self.parser.parse(request)
        email = emails[0]
        payload = json.loads(mandrill_payload_with_attachments_mailbox_2['mandrill_events'])

        self.assertEqual(len(email.attachments), 1)
        self.assertEqual(email.attachments[0][0], '7e357447-3f2e-4c12-a643-5720f30ca7af')
        self.assertEqual(email.attachments[0][2], 'image/jpeg')
        self.assertEqual(
            email.attachments[0][1],
            # the content is base64-decoded, even if the base64 flag is off in the request
            base64.b64decode(
                payload[0]['msg']['images']
                ['7e357447-3f2e-4c12-a643-5720f30ca7af']['content']
            )
        )

    def test_parse_valid_request(self):
        """
        Test a valid POST returns 200 and email(s) are correctly parsed
        """
        request = self.factory.post(self.url, data=mandrill_payload)
        emails = self.parser.parse(request)
        self._assertEmailParsedCorrectly(emails, mandrill_payload)

    def test_parse_valid_request__with_attachments(self):
        request = self.factory.post(self.url, data=mandrill_payload_with_attachments)
        emails = self.parser.parse(request)
        self._assertEmailParsedCorrectly(emails, mandrill_payload_with_attachments)

    @override_settings(INBOUND_MANDRILL_AUTHENTICATION_KEY='mandrill_key')
    def test_parse_valid_request__with_signature(self):
        signature = self._calculate_signature(
            url='http://testserver' + self.url,
            data=mandrill_payload.items(),
            key='mandrill_key',
        )
        request = self.factory.post(
            self.url,
            data=mandrill_payload,
            HTTP_X_MANDRILL_SIGNATURE=signature,
        )
        emails = self.parser.parse(request)
        self._assertEmailParsedCorrectly(emails, mandrill_payload)

    @override_settings(INBOUND_MANDRILL_AUTHENTICATION_KEY='mandrill_key')
    def test_parse_valid_request__with_invalid_signature(self):
        signature = 'invalid_signature'
        request = self.factory.post(
            self.url,
            data=mandrill_payload,
            HTTP_X_MANDRILL_SIGNATURE=signature,
        )
        self.assertRaises(
            MandrillSignatureMismatchError,
            self.parser.parse,
            request,
        )

    def _process_dump(self, foo):
        dump = json.loads(self.payload['mandrill_events'])
        foo(dump)
        return json.dumps(dump)

    def test_parse_invalid_request(self):
        """Test that an invalid request raises RequestParseError."""
        _process = lambda dump: dump[0]['msg'].pop('from_email', None)

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
        request = self.factory.post(self.url, data=self.payload_with_attachments)
        # should except
        with self.assertRaises(AttachmentTooLargeError):
            self.parser.parse(request)

    def test_correspondent_field_parsing(self):
        """Test the speific address parsing of the Mandrill backend"""
        # Addresses https://github.com/yunojuno/django-inbound-email/issues/20

        for input_data, attr_name, expected in [
            # TO / CC / BCC -- all handled by the same method: _get_recipients()
            (
                [['jed@whitehouse.gov', "Jed Bartlet"]],
                "to",
                ['"Jed Bartlet" <jed@whitehouse.gov>'],
            ),
            (
                [
                    ['jed@whitehouse.gov', "Jed Bartlet"],
                    ['toby@whitehouse.gov', "Toby Ziegler"]],
                "to",
                [
                    '"Jed Bartlet" <jed@whitehouse.gov>',
                    '"Toby Ziegler" <toby@whitehouse.gov>'
                ],
            ),
            (
                [['jed@whitehouse.gov', "Bartlet, Jed"]],
                "to",
                ['"Bartlet, Jed" <jed@whitehouse.gov>'],
            ),
            (
                [
                    ['jed@whitehouse.gov', "Bartlet, Jed"],
                    ['toby@whitehouse.gov', "Ziegler, Toby"]],
                "to",
                [
                    '"Bartlet, Jed" <jed@whitehouse.gov>',
                    '"Ziegler, Toby" <toby@whitehouse.gov>'
                ],
            ),
            (
                [['jed@whitehouse.gov', None]],
                "to",
                ['jed@whitehouse.gov'],
            ),
            (
                [
                    ['jed@whitehouse.gov', None],
                    ['toby@whitehouse.gov', None]],
                "to",
                [
                    'jed@whitehouse.gov',
                    'toby@whitehouse.gov'
                ],
            ),
            (
                [['jed@whitehouse.gov', '']],
                "to",
                ['jed@whitehouse.gov'],
            ),
            (
                [
                    ['jed@whitehouse.gov', ''],
                    ['toby@whitehouse.gov', '']
                ],
                "to",
                [
                    'jed@whitehouse.gov',
                    'toby@whitehouse.gov'
                ],
            ),

            # FROM - handled by a _get_sender() method
            # NB: 1) we do not get back a list.
            # 2) _get_sender expects email and name as args
            (
                ['jed@whitehouse.gov', "Jed Bartlet"],
                "from_email",
                '"Jed Bartlet" <jed@whitehouse.gov>',
            ),
            (
                ['jed@whitehouse.gov', "Bartlet, Jed"],
                "from_email",
                '"Bartlet, Jed" <jed@whitehouse.gov>',
            ),
            (
                ['jed@whitehouse.gov', ""],
                "from_email",
                'jed@whitehouse.gov',
            ),
            (
                ['jed@whitehouse.gov', None],
                "from_email",
                'jed@whitehouse.gov',
            ),

            # Handling edge-case or invalid content
            (
                # Latin 1 example
                [['sīla@exañple.com', "McTøst, Sīla"]],
                "to",
                ['"McTøst, Sīla" <sīla@exañple.com>'],
            ),
        ]:

            if attr_name == 'from_email':
                # _get_sender expects a two-tuple of args and returns a string
                output = self.parser._get_sender(*input_data)
            else:
                # _get_recipients expects a list of lists and returns a list of strings
                _results = self.parser._get_recipients(input_data)
                output = [x for x in _results]

            self.assertEqual(
                output,
                expected,
                "Failed to get %s for '%s' %s -- got %s" % (
                    expected, attr_name, input_data, output
                )
            )
