# Signals definitions for django-inbound-email
from django.dispatch import Signal

# this is fired when a new email has been successfully parsed
# from the inbound view function.
email_received = Signal(providing_args=['email', 'request'])
