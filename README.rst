django-inbound
==============

An inbound email handler for Django.

**Current Status**

.. image:: https://travis-ci.org/yunojuno/django-inbound-email.svg?branch=master
    :target: https://travis-ci.org/yunojuno/django-inbound-email

We have a working implementation, with SendGrid, Mailgun and Mandrill backends.
(Both SendGrid and Mandrill have been used in production environments.)

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

Contained within this project is the django app itself, together with
a working Django project that uses the app, and is separately deployable
to Heroku for testing purposes. The app has good test coverage, but it's
really very hard to test inbound emails without having real data, and
that requires a public endpoint that you can use to hook up your
preferred email provider's webhooks.

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

If an email is unacceptable in some way (e.g. an attachment is too large),
then the ``email_received_unacceptable`` signal is fired instead. This signal
has an argument ``exception`` describing the problem.

Installation
------------

For use as the app in Django project, use ``pip``:

.. code:: shell

    $ pip install django-inbound-email

For hacking on the project, pull from Git:

.. code:: shell

    $ git pull git@github.com:yunojuno/django-inbound-email.git
    $ cd django-inbound-email
    django-inbound-email$
    # use virtualenvwrapper, and install Django to allow tests to run
    django-inbound-email$ mkvirtualenv django-inbound-email
    (django-inbound-email) django-inbound-email$ pip install django

Usage
-----

Your main concern, after installing and configuring the app, is handling
the ``email_received`` signal:

.. code:: python

    # This snippet goes somewhere inside your project,
    # wherever you need to react to incoming emails.
    import logging
    from django_inbound_email.signals import email_received

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

Handling file attachments as FileField properties
-------------------------------------------------

There is one gotcha in the handling of file attachments. The email
object that is sent via the signal has an ``attachments`` property,
but this contains a list of 3-tuples [(name, contents, content_type),],
not a list of file objects. In order to store the attachments against
a model as a FileField, you'll need to convert the tuples back into
something that Django can deal with.

.. code:: python

    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.db import models

    from django_inbound_email.signals import email_received


    def get_file(attachment):
        """Convert email.attachment tuple into a SimpleUploadedFile."""
        name, content, content_type = attachment
        return SimpleUploadedFile(name, content, content_type)


    class Example(models.Model):
        """Example model that contains a FileField property."""
        file = models.FileField()


    def on_email_received(sender, **kwargs):
        """Handle inbound emails."""
        email = kwargs.pop('email')
        for attachment in email.attachments:
            # we must convert attachment tuple into a file
            # before adding as the property.
            example = Example(file=get_file(attachment))
            example.save()


Tests
-----

There is a test django project, ``test_app`` that is used to run the
tests.

.. code:: shell

    (django-inbound-email) django-inbound-email$ python manage.py test

Configuration
-------------

-  Install the app
-  Add the app to ``INSTALLED_APPS``
-  Add ``INBOUND_EMAIL_PARSER`` setting
-  Update your provider configuration to point to app URL

.. code:: python

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
-  Pluggable backends (SendGrid, Mailgun and Mandrill currently supported)
-  Handle character encodings properly
-  Handle attachments, including if they are too large

Things it (probably) won't do:

-  Handle email reply parsing - use
   https://github.com/zapier/email-reply-parser
