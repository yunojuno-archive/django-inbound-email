"""Main project URL definitions."""
from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(
        r'^emails/',
        include('django_inbound_email.urls')
    )
)
