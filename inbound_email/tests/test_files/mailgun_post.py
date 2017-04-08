# test contents taken from the Mailgun route tester - https://mailgun.com/cp/routes#
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

test_inbound_payload = {}
test_inbound_payload['stripped-signature']="""Thanks,
Bob"""
test_inbound_payload['From']='Bob <bob@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>'
test_inbound_payload['attachment-count']='2'
test_inbound_payload['To']='Alice <alice@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>'
test_inbound_payload['subject']='Re: Sample POST request'
test_inbound_payload['from']='Bob <bob@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>'
test_inbound_payload['User-Agent']='Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20130308 Thunderbird/17.0.4'
test_inbound_payload['stripped-html']="""<html><head><meta content="text/html; charset=ISO-8859-1" http-equiv="Content-Type"></head><body text="#000000" bgcolor="#FFFFFF">
    <div class="moz-cite-prefix">
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);">Hi Alice,</div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);"><br></div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);">This is Bob.<span class="Apple-converted-space">&#160;<img alt="" src="cid:part1.04060802.06030207@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org" height="15" width="33"></span></div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);"><br>
        I also attached a file.<br><br></div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);">Thanks,</div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);">Bob</div>
      <br><br></div>
    <br></body></html>"""
test_inbound_payload['In-Reply-To']='<517AC78B.5060404@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>'
test_inbound_payload['Date']='Fri, 26 Apr 2013 11:50:29 -0700'
test_inbound_payload['Message-Id']='<517ACC75.5010709@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>'
test_inbound_payload['body-plain']="""Hi Alice,

This is Bob.

I also attached a file.

Thanks,
Bob

On 04/26/2013 11:29 AM, Alice wrote:
> Hi Bob,
>
> This is Alice. How are you doing?
>
> Thanks,
> Alice

"""
test_inbound_payload['Mime-Version']='1.0'
test_inbound_payload['Received']='from [10.20.76.69] (Unknown [50.56.129.169]) by mxa.mailgun.org with ESMTP id 517acc75.4b341f0-worker2; Fri, 26 Apr 2013 18:50:29 -0000 (UTC)'
test_inbound_payload['content-id-map']='{"<part1.04060802.06030207@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>": "attachment-1"}'
test_inbound_payload['Sender']='bob@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org'
test_inbound_payload['timestamp']='1412239366'
test_inbound_payload['message-headers']='[["Received", "by luna.mailgun.net with SMTP mgrt 8788212249833; Fri, 26 Apr 2013 18:50:30 +0000"], ["Received", "from [10.20.76.69] (Unknown [50.56.129.169]) by mxa.mailgun.org with ESMTP id 517acc75.4b341f0-worker2; Fri, 26 Apr 2013 18:50:29 -0000 (UTC)"], ["Message-Id", "<517ACC75.5010709@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>"], ["Date", "Fri, 26 Apr 2013 11:50:29 -0700"], ["From", "Bob <bob@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>"], ["User-Agent", "Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20130308 Thunderbird/17.0.4"], ["Mime-Version", "1.0"], ["To", "Alice <alice@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>"], ["Subject", "Re: Sample POST request"], ["References", "<517AC78B.5060404@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>"], ["In-Reply-To", "<517AC78B.5060404@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>"], ["X-Mailgun-Variables", "{\"my_var_1\": \"Mailgun Variable #1\", \"my-var-2\": \"awesome\"}"], ["Content-Type", "multipart/mixed; boundary=\"------------020601070403020003080006\""], ["Sender", "bob@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org"]]'
test_inbound_payload['stripped-text']="""Hi Alice,

This is Bob.

I also attached a file."""
test_inbound_payload['recipient']='alice@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org'
test_inbound_payload['sender']='bob@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org'
test_inbound_payload['X-Mailgun-Variables']='{"my_var_1": "Mailgun Variable #1", "my-var-2": "awesome"}'
test_inbound_payload['token']='4166ec05b27b5d3c024252ad43df47865128c8fcde47dfea6b'
test_inbound_payload['body-html']="""<html>
  <head>
    <meta content="text/html; charset=ISO-8859-1"
      http-equiv="Content-Type">
  </head>
  <body text="#000000" bgcolor="#FFFFFF">
    <div class="moz-cite-prefix">
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);">Hi Alice,</div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);"><br>
      </div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);">This is Bob.<span class="Apple-converted-space">&nbsp;<img
            alt="" src="cid:part1.04060802.06030207@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org"
            height="15" width="33"></span></div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);"><br>
        I also attached a file.<br>
        <br>
      </div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);">Thanks,</div>
      <div style="color: rgb(34, 34, 34); font-family: arial,
        sans-serif; font-size: 12.666666984558105px; font-style: normal;
        font-variant: normal; font-weight: normal; letter-spacing:
        normal; line-height: normal; orphans: auto; text-align: start;
        text-indent: 0px; text-transform: none; white-space: normal;
        widows: auto; word-spacing: 0px; -webkit-text-size-adjust: auto;
        -webkit-text-stroke-width: 0px; background-color: rgb(255, 255,
        255);">Bob</div>
      <br>
      On 04/26/2013 11:29 AM, Alice wrote:<br>
    </div>
    <blockquote cite="mid:517AC78B.5060404@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org" type="cite">Hi
      Bob,
      <br>
      <br>
      This is Alice. How are you doin©?
      <br>
      <br>
      Thanks,
      <br>
      Alice
      <br>
    </blockquote>
    <br>
  </body>
</html>
"""
test_inbound_payload['References']='<517AC78B.5060404@sandbox085a3b878a964897b9b9efb2395a1f5a.mailgun.org>'
test_inbound_payload['signature']='b220bb34b816a1b00512e1a288ac9b8e5808c51de773bc13628547486eb3a80d'
test_inbound_payload['Content-Type']='multipart/mixed; boundary="------------020601070403020003080006"'
test_inbound_payload['Subject']='Re: Sample POST request'
