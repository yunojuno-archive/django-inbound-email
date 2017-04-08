# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r'^inbound/$',
        views.receive_inbound_email,
        name='receive_inbound_email'
    )
]
