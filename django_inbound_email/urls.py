from django.conf.urls import patterns, url

urlpatterns = patterns(
    'django_inbound_email.views',
    url(
        r'^inbound/$',
        'receive_inbound_email',
        name='receive_inbound_email'
    ),
)
