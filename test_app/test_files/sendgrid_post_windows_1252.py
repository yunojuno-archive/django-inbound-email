# -*- coding: windows-1252 -*-
test_inbound_payload_1252 = {}
test_inbound_payload_1252['text'] = """This is a message in windows-1252 encoding. åßœ∑´¥¨¨^"""
test_inbound_payload_1252['charsets'] = '{"to":"UTF-8","html":"utf-8","subject":"UTF-8","from":"UTF-8","text":"windows-1252"}'
test_inbound_payload_1252['subject'] = 'test'
test_inbound_payload_1252['to'] = '<to@example.com>'
test_inbound_payload_1252['cc'] = '<b@example.com>, <c@example.com>'
test_inbound_payload_1252['from'] = 'Hugo Rodger-Brown <from@example.com>'
