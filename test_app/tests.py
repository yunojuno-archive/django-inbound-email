# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.test import TestCase

from django_inbound_email.signals import email_received
from django_inbound_email.views import receive_inbound_email

from test_app.test_files.sendgrid_post import test_inbound_payload


class SendGridTests(TestCase):
    """Tests for SendGridRequestParser."""

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.url = reverse('receive_inbound_email')
        settings.INBOUND_EMAIL_BACKEND = 'django_inbound_email.backends.sendgrid.SendGridRequestParser'

    def test_parse_valid_request(self):
        """Test that a valid POST returns a 200."""
        response = self.client.post(self.url, data=test_inbound_payload)
        self.assertContains(
            response,
            "Successfully parsed inbound email.",
            status_code=200
        )

    def test_parse_invalid_request_200(self):
        """Test that an invalid POST returns a 200, if so configured."""
        settings.INBOUND_EMAIL_RESPONSE_200 = True
        response = self.client.post(self.url, data={})
        self.assertContains(
            response,
            "Unable to parse inbound email",
            status_code=200
        )

    def test_parse_invalid_request_400(self):
        """Test that an invalid POST returns a 400 if so configured."""
        settings.INBOUND_EMAIL_RESPONSE_200 = False
        from django_inbound_email.views import receive_inbound_email
        response = self.client.post(self.url, data={})
        self.assertContains(
            response,
            "Unable to parse inbound email",
            status_code=400
        )

    def test_email_received_signal(self):
        """Test that a valid POST fires the email_received signal."""

        self.request = self.factory.post(self.url, data=test_inbound_payload)

        def on_email_received(sender, **kwargs):
            self.on_email_received_fired = True
            self.assertIsNone(sender)
            request = kwargs.pop('request', None)
            email = kwargs.pop('email', None)
            self.assertIsNotNone(request)
            self.assertEqual(request, self.request)
            self.assertIsNotNone(email, None)
            self.assertEqual(email.to, test_inbound_payload['to'].split(','))
            self.assertEqual(email.from_email, test_inbound_payload['from'])
            self.assertEqual(email.subject, test_inbound_payload['subject'])
            self.assertEqual(email.body, test_inbound_payload['text'])
            self.assertEqual(email.cc, test_inbound_payload['cc'].split(','))
            self.assertEqual(len(email.alternatives), 1)
            self.assertEqual(email.alternatives[0][0], test_inbound_payload['html'])

        self.on_email_received_fired = False
        email_received.connect(on_email_received)
        self.assertFalse(self.on_email_received_fired)

        # fire a request in to force the signal to fire
        response = receive_inbound_email(self.request)
        self.assertTrue(self.on_email_received_fired)
        self.assertTrue(response.status_code==200)
        # clean up after ourselves
        email_received.disconnect(on_email_received)

    def test_text_email_only(self):
        """Test inbound email with no HTML alternative."""
        data = test_inbound_payload
        data['html'] = ""
        self.request = self.factory.post(self.url, data=data)

        def on_email_received(sender, **kwargs):
            email = kwargs.pop('email', None)
            self.assertEqual(len(email.alternatives), 0)

        email_received.connect(on_email_received)
        response = receive_inbound_email(self.request)
        email_received.disconnect(on_email_received)
        self.assertContains(
            response,
            "Successfully parsed inbound email.",
            status_code=200
        )

    def test_attachments(self):
        """Test inbound email with attachments."""
        self.fail("Write test for email attachments.")

    def test_encodings(self):
        """Test inbound email with non-UTF8 encoded fields."""
        self.fail("Write test for non-default encodings.")
