#!/usr/bin/python
# coding: utf-8
from datetime import datetime
from threading import Timer
import argparse
import dateparser
import multiprocessing
import sys
import logging
import getpass

import sleekxmpp

from sio import get_menu
from reisapi import get_departures


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
                message = get_menu()
                self.send_message(mto=msg['from'].bare, mbody=message, mtype="groupchat")

            if msg['body'].startswith("!lunch "):
                restaurant = msg['body'].split(" ", 1)[1]
                menu = get_menu(restaurant)
                if menu:
                    message = menu
                else:
                    message = "Unable to get menu :("
                self.send_message(mto=msg['from'].bare, mbody=message, mtype="groupchat")

            if msg['body'] == "!ruter":
                for platform, departures in get_departures().items():
                    message = "Platform {}: ".format(platform)
                    message += "; ".join(departures)
                    self.send_message(mto=msg['from'].bare, mbody=message, mtype="groupchat")

            if msg['body'].startswith("!reminder "):
                now = datetime.now()
                max_seconds = 3600 * 24 * 7  # Do not create reminders > 1 week
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
                else:
                    date = date.replace(microsecond=0)

                seconds = (date - now).total_seconds()

                if seconds < 0:
                    self.send_message(mto=msg['from'].bare, mbody="Error. Can't remind you in the past.", mtype="groupchat")
                    return
                elif seconds > max_seconds:
                    self.send_message(mto=msg['from'].bare, mbody="Error. Please set reminder to less than 1 week.", mtype="groupchat")
                    return

                print("Reminder in {} sec at {}.".format(seconds, date.isoformat()))
                self.send_message(mto=msg['from'].bare, mbody="Reminder set at %s" % date.isoformat(), mtype="groupchat")
                Timer(seconds, self.send_message, kwargs={"mto": msg['from'].bare, "mbody": message, "mtype": "groupchat"}).start()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            msg.reply("I'm a bot. Hurr durr.").send()


class MyBotProcess(multiprocessing.Process):

    def __init__(self, xmpp):
        self.xmpp = xmpp
        super().__init__()

    def run(self):
        xmpp.register_plugin('xep_0030')  # Service Discovery
        xmpp.register_plugin('xep_0045')  # Multi-User Chat
        xmpp.register_plugin('xep_0199')  # XMPP Ping
        if xmpp.connect():
            xmpp.process(block=True)
            print("Done")
        else:
            print("Unable to connect.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-q", "--quiet", help="set logging to ERROR", action="store_const", dest="loglevel", const=logging.ERROR, default=logging.INFO)
    parser.add_argument("-d", "--debug", help="set logging to DEBUG", action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)
    parser.add_argument("-j", "--jid", dest="jid", help="JID to use")
    parser.add_argument("-r", "--room", dest="room", help="MUC room to join")
    parser.add_argument("-n", "--nick", dest="nick", help="MUC nickname")

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel, format='%(levelname)-8s %(message)s')

    if args.jid is None:
        args.jid = input("JID: ")
    if args.room is None:
        args.room = input("MUC room: ")
    if args.nick is None:
        args.nick = input("MUC nickname: ")

    password = getpass.getpass("Password: ")

    xmpp = MyBot(args.jid, password, args.room, args.nick)
    p = MyBotProcess(xmpp)
    p.start()
    try:
        p.join()
    except KeyboardInterrupt as e:
        pass
