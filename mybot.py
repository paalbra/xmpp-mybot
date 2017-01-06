#!/usr/bin/python
#coding: utf-8
from datetime import datetime
from optparse import OptionParser
from pprint import pprint
from threading import Timer
import dateparser
import sys
import logging
import getpass

import sleekxmpp

from sio import get_sio_dinner
from reisapi import get_departures

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

class MyBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("message", self.message)

    def start(self, event):
        self.get_roster()
        self.send_presence(ppriority=-100)
        self.plugin['xep_0045'].joinMUC(self.room, self.nick, wait=True)

    def muc_message(self, msg):
        if msg['mucnick'] != self.nick:

            if msg['body'] == "!lunch":
                message = get_sio_dinner()
                self.send_message(mto=msg['from'].bare, mbody=message, mtype="groupchat")

            if msg['body'] == "!ruter":
                for platform, departures in get_departures().iteritems():
                    message = "Platform {}: ".format(platform)
                    message += "; ".join(departures)
                    self.send_message(mto=msg['from'].bare, mbody=message, mtype="groupchat")

            if msg['body'].startswith("!reminder "):
                now = datetime.now()
                try:
                    date_string, message = [s.strip() for s in msg['body'][10:].split(";", 1)]
                except:
                    self.send_message(mto=msg['from'].bare, mbody="Error. Expected: \"!reminder <date/time string>; <reminder message>\" ", mtype="groupchat")
                    return

                date = dateparser.parse(date_string, settings={'PREFER_DATES_FROM': 'future'})
                message = "%s: %s" % (msg["from"].resource, message)

                if date is None:
                    self.send_message(mto=msg['from'].bare, mbody="Error. Weird date/time. Docs: https://dateparser.readthedocs.io/en/latest/", mtype="groupchat")
                    return

                seconds = (date - now).total_seconds()

                if seconds < 0:
                    self.send_message(mto=msg['from'].bare, mbody="Error. Can't remind you in the past.", mtype="groupchat")
                    return
                elif seconds > 3600:
                    self.send_message(mto=msg['from'].bare, mbody="Error. Please set reminder to less than 1 hour.", mtype="groupchat")
                    return

                print("Reminder in %d sec at %s." % (seconds, date.isoformat()))
                self.send_message(mto=msg['from'].bare, mbody="Reminder set at %s" % date.isoformat(), mtype="groupchat")
                Timer(seconds, self.send_message, kwargs={"mto": msg['from'].bare, "mbody": message, "mtype": "groupchat"}).start()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            msg.reply("I'm a bot. Hurr durr.").send()

if __name__ == '__main__':
    optp = OptionParser()

    optp.add_option('-q', '--quiet', help='set logging to ERROR', action='store_const', dest='loglevel', const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    optp.add_option("-j", "--jid", dest="jid", help="JID to use")
    optp.add_option("-r", "--room", dest="room", help="MUC room to join")
    optp.add_option("-n", "--nick", dest="nick", help="MUC nickname")

    opts, args = optp.parse_args()

    logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("JID: ")
    if opts.room is None:
        opts.room = raw_input("MUC room: ")
    if opts.nick is None:
        opts.nick = raw_input("MUC nickname: ")
    
    password = getpass.getpass("Password: ")

    xmpp = MyBot(opts.jid, password, opts.room, opts.nick)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping

    # Connect to the XMPP server and start processing XMPP stanzas.
    if xmpp.connect():
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")

