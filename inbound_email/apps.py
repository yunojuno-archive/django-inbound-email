# -*- coding: utf-8 -*-
from django.apps import AppConfig


class InboundEmailAppConfig(AppConfig):

    """AppConfig for Django-Onfido."""

    name = 'inbound_email'
    verbose_name = "Inbound Email"
    configs = []

    def ready(self):
        """Validate config and connect signals."""
        super(InboundEmailAppConfig, self).ready()
