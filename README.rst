django-inbound
==============

An inbound email handler for Django.

**Current Status**

.. image:: https://travis-ci.org/yunojuno/django-inbound-email.svg?branch=master
    :target: https://travis-ci.org/yunojuno/django-inbound-email

We have a working implementation, with a SendGrid backend.

The test_app is deployed to Heroku and any emails sent to
anything@django-inbound-email.yunojuno.com will be parsed by a live version of
the test_app.

This test app just does a bounceback - any incoming email to that address
is sent back to the sender's address. This makes it easy to test 'real-world'
email examples. Please feel free to send email to that address - and if you're
using Outlook 97 on Windows XP, in China, then we'd really like to hear from
you. You don't hear that much on Github.

NB The app deployed on Heroku currently sends the bouncebacks using the
Mailtrap app, so you won't actually receive the email, but I can give limited
access to contributors so that they can see them all. I'll truncate the Mailtrap
inbox at irregular intervals.

What?
-----

A Django app to make it easy to receive inbound emails from users via a
hosted transactional email service (e.g. SendGrid, Postmark, Mandrill,
etc.)

Why?
----

If your project accepts inbound emails, you are probably using one of
the big transactional email providers.

These services all provide a mechanism for receiving inbound emails
which involves them (the service) parsing the inbound email and then
posting the contents to an HTTP endpoint in your project. This is a
great service, but it can often be fiddly to integrate into your app and
it reinforces service lock-in, as each service's callback is slightly
different.

There is also a significant SMTP-HTTP 'impedance mismatch'. You send
emails through Django's (SMTP) mail library, which provides the
EmailMessage and EmailMultiAlternative objects, but you receive emails
as an HTTP POST. Wouldn't it be nice if you could both send and receive
Django objects?

This app converts the incoming HttpRequest back into an
EmailMultiAlternatives object, and fires a signal that sends both the
new object, and the original request object. You simply have to listen
for this signal, and process the email as your application requires.

The mail parser handles non-UTF-8 character sets (so those pesky PC
Outlook emails don't come through all garbled), and file attachments.

How?
----

Although this is Django app, it contains (for now) no models. Its
principle component is a single view function that does the parsing.
There is a single configuration setting - ``INBOUND_EMAIL_PARSER``,
which must be one of the supported backends.

This setting is expected to be available to the app from ``django.conf.settings``,
and the app will raise an error if it does not exist.

The default URL for inbound emails is simply '/inbound/'.

The flow through the app is very simple:

1. The app view function ``receive_inbound_email`` is called when a new email
   POST is received from your service provider.
2. This function looks up the ``INBOUND_EMAIL_PARSER``, loads the
   appropriate backend, and parses the ``request.POST`` contents out
   into a new ``django.core.mail.EmailMultiAlternatives`` object.
3. The ``email_received`` signal is fired, and the new
   ``EmailMultiAlternatives`` instance is passed, along with the
   original ``HttpRequest`` (in case there's any special handling that
   you require - e.g. DKIM / SPF info, if your provider passes that
   along).

Your main concern, after installing and configuring the app, is handling
the ``email_received`` signal:

.. code:: python

    # This snippet goes somewhere inside your project,
    # wherever you need to react to incoming emails.
    import logging
    from django_inbound.signals import email_received

    def on_email_received(sender, **kwargs):
        """Handle inbound emails."""
        email = kwargs.pop('email')
        request = kwargs.pop('request')

        # your code goes here - save the email, respond to it, etc.
        logging.debug(
            "New email received from %s: %s",
            email.from_email,
            email.subject
        )

    # pass dispatch_uid to prevent duplicates:
    # https://docs.djangoproject.com/en/dev/topics/signals/
    email_received.connect(on_email_received, dispatch_uid="something_unique")

Installation
------------

For use as the app in Django project, use ``pip``:

::

    $ pip install django-inbound-email

For hacking on the project, pull from Git:

::

    $ git pull git@github.com:yunojuno/django-inbound-email.git
    $ cd django-inbound-email
    django-inbound-email$
    # use virtualenvwrapper, and install Django to allow tests to run
    django-inbound-email$ mkvirtualenv django-inbound-email
    (django-inbound-email) django-inbound-email$ pip install django

Tests
-----

There is a test django project, ``test_app`` that is used to run the
tests.

::

    (django-inbound-email) django-inbound-email$ python manage.py test

Configuration
-------------

-  Install the app
-  Add the app to ``INSTALLED_APPS``
-  Add ``INBOUND_EMAIL_PARSER`` setting
-  Update your provider configuration to point to app URL

::

    # the fully-qualified path to the provider's backend parser
    INBOUND_EMAIL_PARSER = 'django_inbound_email.backends.sendgrid.SendGridRequestParser'

    # if True (default=False) then log the contents of each inbound request
    INBOUND_EMAIL_LOG_REQUESTS = True

    # if True (default=True) then always return HTTP status of 200 (may be required by provider)
    INBOUND_EMAIL_RESPONSE_200 = True

    # add the app to Django's INSTALL_APPS setting
    INSTALLED_APPS = (
        # other apps
        # ...
        'django_inbound_email',
    )


Features
--------

Things it will do:

-  Parse HTTP requests into EmailMultiAlternatives objects
-  Pluggable backends (SendGrid only on launch)
-  Handle character encodings properly
-  Handle attachments

Things it (probably) won't do:

-  Handle email reply parsing - use
   https://github.com/zapier/email-reply-parser
