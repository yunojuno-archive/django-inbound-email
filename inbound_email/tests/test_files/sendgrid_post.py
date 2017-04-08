test_inbound_payload = {}
test_inbound_payload['text'] = """This is a message.


Sent with Unibox



"""
test_inbound_payload['charsets'] = '{"to":"UTF-8","html":"utf-8","subject":"UTF-8","from":"UTF-8","text":"utf-8"}'
test_inbound_payload['subject'] = 'test'
test_inbound_payload['to'] = '<to@example.com>'
test_inbound_payload['cc'] = '<b@example.com>, <c@example.com>'
test_inbound_payload['spam_score'] = '0.266'
test_inbound_payload['html'] = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><head><title></title></head><body><div>This is a message.
</div><div><br></div><div class="unibox-signature">Sent with <a href="http://www.uniboxapp.com/t/sig">Unibox</a>
</div></body></html>"""
test_inbound_payload['from'] = 'Hugo Rodger-Brown <from@example.com>'
test_inbound_payload['sender_ip'] = '74.125.82.43'
test_inbound_payload['attachment-info'] = '{"attachment1":{"filename":"Screen Shot 2014-05-12 at 17.06.14.png","name":"Screen Shot 2014-05-12 at 17.06.14.png","type":"image/png"}}'
test_inbound_payload['envelope'] = '{"to":["to@example.com"],"from":"from@example.com"}'
test_inbound_payload['dkim'] = 'none'
test_inbound_payload['SPF'] = 'pass'
test_inbound_payload['headers'] = """Received: by mx-007.sjc1.sendgrid.net with SMTP id og7B28feuJ Tue, 13 May 2014 10:25:40 +0000 (GMT)
Received: from mail-wg0-f43.google.com (mail-wg0-f43.google.com [74.125.82.43]) by mx-007.sjc1.sendgrid.net (Postfix) with ESMTPS id 5FE7FA836D6 for <A1@messages-uat.yunojuno.com>; Tue, 13 May 2014 10:25:39 +0000 (GMT)
Received: by mail-wg0-f43.google.com with SMTP id l18so147281wgh.14 for <to@example.com>; Tue, 13 May 2014 03:25:37 -0700 (PDT)
X-Google-DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=1e100.net; s=20130820; h=x-gm-message-state:from:to:subject:date:message-id:mime-version :content-type; bh=9o+Uxa2TnusbKHc7VtEFg22821Db2LqhnYwxDDCfcKY=; b=LSth5QmBnqBJEgrshQlZ3mBoxut8fiQqoLbk+qdEpi/ZhEcKPTe0zePlBsEGqhAgUK 4HedAUcRqY8okISA+I3Rma9pP0y2lrqpedSrRi8M6y1ywXOyeDY1eVGCO9VqyXk1q4Fo c7xUXkQbRst9CP03BrDTLHcGwzdlbmV1fk/WhJqp2N0DVnYfSaBVF/MRovPdLvLxmuz7 Sbb//SDySNCue3AiyhJ/NEhyrI4CsTJo54fPdhBUkW8GMNurrKoBZVlnDRmRNTXgN8Jz vu8k0yhFeGKCMv5BuosFLaCQAGwzvu6G7NfIfMBLeIloEB5VJrq7ZclzY9EwQOllEbjv i3yA==
X-Gm-Message-State: ALoCoQlleb+6UgRbdYDnkbup4PQhdsCZlpK/KEPBFlKr4jabqxRWQSKNMsfv/lHMq1NTG8sTqB0m
X-Received: by 10.194.87.163 with SMTP id az3mr1760074wjb.63.1399976737521; Tue, 13 May 2014 03:25:37 -0700 (PDT)
Received: from [192.168.0.106] ([217.138.17.50]) by mx.google.com with ESMTPSA id fz11sm21154279wic.4.2014.05.13.03.25.35 for <to@example.com> (version=TLSv1 cipher=ECDHE-RSA-RC4-SHA bits=128/128); Tue, 13 May 2014 03:25:35 -0700 (PDT)
X-Google-Original-Date: 13 May 2014 11:25:36 +0100
From: Hugo Rodger-Brown <from@example.com>
To: <to@example.com>
Subject: test
Date: Tue, 13 May 2014 03:25:35 -0700 (PDT)
Message-Id: <E31C8C77-1EE4-41C9-A503-2C028F224D7C@example.com>
MIME-Version: 1.0
X-Mailer: Unibox (188)
Content-Type: multipart/mixed; boundary="=_C7FE9D5A-F282-4723-97C8-88C72CAE2F38"
"""
test_inbound_payload['spam_report'] = """Spam detection software, running on the system "mx-007.sjc1.sendgrid.net", has
identified this incoming email as possible spam.  The original message
has been attached to this so you can view it (if it isn't spam) or label
similar future email.  If you have any questions, see
the administrator of that system for details.

Content preview:  This is a message. Sent with Unibox This is a message. [...]


Content analysis details:   (0.3 points, 5.0 required)

 pts rule name              description
---- ---------------------- --------------------------------------------------
 0.0 HTML_MESSAGE           BODY: HTML included in message
 0.0 DC_PNG_UNO_LARGO       Message contains a single large inline gif
 0.1 DC_IMAGE_SPAM_TEXT     Possible Image-only spam with little text
 0.1 DC_IMAGE_SPAM_HTML     Possible Image-only spam

"""
test_inbound_payload['attachments'] = '1'
