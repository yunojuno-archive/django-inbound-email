# Contributing

We, as YunoJuno, will be building this app out to support out specific inbound
email requirements - which is primarily around support for SendGrid as a
backend. New features, such as (at the time of writing) support for
attachments, we will be adding at our convenience.

All of which means, if the app isn't currently supporting _your_ use case,
**get involved**!

The usual rules apply:

1. If you see something that's wrong, or something that's missing, open an
issue. NB please take a minute to verify that your issue is not already
covered by an existing issue.

2. If you want to fix something, or add a new feature / backend etc. then:

* Fork the repo
* Run the tests locally: `python manage.py test`
* Create a local branch (ideally named after the related issue, beginning with the issue number, e.g. `1-support-email-attachments`)
* Write some code
* Write some tests to prove your code works
* Commit it
* Send a pull request

Other than that we'll work it out as we go along.
