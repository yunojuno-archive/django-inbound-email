django-inbound
==============

An inbound email handler for Django.

What?
-----

A Django app to make it easy to receive inbound emails from users via a hosted transactional email service (e.g. SendGrid, Postmark, Mandrill, etc.)

Why?
----

If your project accepts inbound emails, you are probably using one of the big transactional email providers.

These services all provide a mechanism for receiving inbound emails which involves them (the service) parsing the inbound email and then posting the contents to an HTTP endpoint in your project. This is a great service, but it can often be fiddly to integrate into your app and it reinforces service lock-in, as each service's callback is slightly different.

There is also a significant SMTP-HTTP 'impedance mismatch'. You send emails through Django's (SMTP) mail library, which provides the EmailMessage and EmailMultiAlternative objects, but you receive emails as an HTTP POST. Wouldn't it be nice if you could both send and receive Django objects?

This app converts the incoming HttpRequest back into an EmailMultiAlternatives object, and fires a signal that sends both the new object, and the original request object. You simply have to listen for this signal, and process the email as your application requires.

The mail parser handles non-UTF-8 character sets (so those pesky PC Outlook emails don't come through all garbled), and file attachments.

How?
----

Although this is Django app, it contains (for now) no models. Its principle component is a single view function that does the parsing. There is a single configuration setting - `INBOUND_EMAIL_PROVIDER`, which must be one of the supported backends (default will be 'SendGrid' as that's what we use). This setting is expected to be available to the app from `django.conf.settings`, and the app will raise an error if it does not exist.

The default URL for inbound emails is simply '/inbound/'.

The flow through the app is very simple:

1. The app view function `receive_inbound` is called when a new email POST is received from your service provider.
2. This function looks up the `INBOUND_EMAIL_PROVIDER`, loads the appropriate backend, and parses the `request.POST` contents out into a new `django.core.mail.EmailMultiAlternatives` object.
3. The `email_received` signal is fired, and the new `EmailMultiAlternatives` instance is passed, along with the original `HttpRequest` (in case there's any special handling that you require - e.g. DKIM / SPF info, if your provider passes that along).

Your main concern, after installing and configuring the app, is handling the `email_received` signal:

```python
# This snippet goes somewhere inside your project,
# wherever you need to react to incoming emails.
import logging
from django_inbound.signals import email_received

def on_email_received(sender, instance, request, **kwargs):
    """Handle inbound emails."""
    # your code goes here - save the email, respond to it, etc.
    logging.debug(
        "New email received from %s: %s",
        instance.from_email,
        instance.subject
    )

# pass dispatch_uid to prevent duplicates:
# https://docs.djangoproject.com/en/dev/topics/signals/
email_received.connect(on_email_received, dispatch_uid="something_unique")
```

Installation
------------

Via `pip` - details to follow.

Tests
-----

There will be some.


Configuration
-------------

* Install the app
* Add the app to INSTALLED_APPS
* Add INBOUND_EMAIL_PROVIDER setting
* Update your provider configuration to point to app URL

Features
--------

Things it will do:

* Parse HTTP requests into EmailMultiAlternatives objects
* Pluggable backends (SendGrid only on launch)
* Handle character encodings properly
* Handle attachments

Things it (probably) won't do:

* Handle email reply parsing - use https://github.com/zapier/email-reply-parser


Progress to date
----------------

This doesn't exist yet, as we are waiting till we finish our current workload before building this.

All the functionality exists within our own project (www.yunojuno.com), it just needs extracting into a separate app, a setup.py, registration with PyPI, and so on... It'll land in May. Possibly.
