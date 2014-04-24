django-inbound
==============

An inbound email handler for Django.

What
----

A Django app to make it easy to receive inbound emails from users via a hosted transactional email service (e.g. SendGrid, Postmark, Mandrill, etc.)

Why?
----

If your project accepts inbound emails, you are probably using one of the big transactional email providers.

These services all provide a mechanism for receiving inbound emails which involved them (the service) parsing the inbound email and then posting the contents to an HTTP endpoint in your project. This is a great service, but it can often be fiddly to integrate into your app, and it reinforces service lock-in, as each service's callback is slightly different.

There is also a significant "SMTP-HTTP impedance mismatch". You send emails through Django's (SMTP) mail library, which provides the EmailMessage and EmailMultiAlternative objects, but you receive emails as standard (HTTP) HttpRequest.POST properties. Wouldn't it be nice if you both send and received Django objects?

This project provides a simple wrapper that converts the incoming HttpRequest back into an EmailMultiAlternatives object, and raises a Django signal that can be hooked into.

