#!/usr/bin/python
# coding: utf-8
from datetime import datetime
from threading import Timer
import argparse
import configparser
import dateparser
import multiprocessing
import threading
import time
import logging
import getpass
import re

import schedule
import sleekxmpp

from sio import get_menu, get_restaurant_names
from reisapi import get_departures


class MyBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.command_prefix = "!"

        self.schedule_scheduler = schedule.Scheduler()

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("message", self.message)

    def start(self, event):
        self.get_roster()
        self.send_presence(ppriority=-100)
        self.plugin['xep_0045'].joinMUC(self.room, self.nick, wait=True)

        def run_continuously():
            while True:
                self.schedule_scheduler.run_pending()
                time.sleep(1)

        continuous_thread = threading.Thread(target=run_continuously)
        continuous_thread.start()

    def muc_message(self, msg):
        if msg['mucnick'] == self.nick:
            # Ignore messages made by self
            return

        if msg['body'].startswith(self.command_prefix):
            message = msg['body'][len(self.command_prefix):]
            match = re.match("(?P<command>[a-z]+)(?P<argument>.*)?", message)
            if not match:
                # This is not a command
                return
            command = match.group("command")
            argument = match.group("argument").strip()

        logging.debug(f"Got command '{command}' with argument '{argument}'")

        if command == "lunch":
            if not argument:
                response = get_menu()
            else:
                restaurant_name = argument
                restaurant = get_restaurant_names(restaurant_name)
                if not restaurant:
                    response = "No such restaurant"
                elif len(restaurant) > 1:
                    restaurant_names = ", ".join(restaurant)
                    response = "Did you mean?: {}".format(restaurant_names)
                else:
                    # Single restaurant
                    menu = get_menu(restaurant[0])
                    if menu:
                        response = "{}: {}".format(restaurant[0], menu)
                    else:
                        response = "Unable to get menu from: {}".format(restaurant[0])
            self.send_message(mto=msg['from'].bare, mbody=response, mtype="groupchat")

        if command == "schedule":
            response = None

            # TODO: Fix this horrible hacky command

            if argument == "jobs":
                for job in self.schedule_scheduler.jobs or ["No jobs"]:
                    self.send_message(mto=msg['from'].bare, mbody=str(job), mtype="groupchat")
            if argument.startswith("every "):
                try:
                    _, day, time, text = argument.split(" ", 3)
                    if day not in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
                        raise Exception
                    job = self.schedule_scheduler.every()
                    job.start_day = day
                    job.weeks.at(time).do(self.send_message, mto=msg['from'].bare, mbody=text, mtype="groupchat")
                    response = "Job added"
                except Exception as e:
                    response = "Error"
                    pass
            if argument == "clear":
                self.schedule_scheduler.clear()
                response = "Schedule cleared"

            if response:
                self.send_message(mto=msg['from'].bare, mbody=response, mtype="groupchat")

        if command == "ruter":
            for platform, departures in get_departures().items():
                response = "Platform {}: ".format(platform)
                response += "; ".join(departures)
                self.send_message(mto=msg['from'].bare, mbody=response, mtype="groupchat")

        if command == "reminder":
            now = datetime.now()
            max_seconds = 3600 * 24 * 7  # Do not create reminders > 1 week
            try:
                date_string, text = [s.strip() for s in argument.split(";", 1)]
            except:
                self.send_message(mto=msg['from'].bare, mbody="Error. Expected: \"!reminder <date/time string>; <reminder text>\" ", mtype="groupchat")
                return

            date = dateparser.parse(date_string, settings={'PREFER_DATES_FROM': 'future'})
            response = "%s: %s" % (msg["from"].resource, text)

            if date is None:
                self.send_message(mto=msg['from'].bare, mbody="Error. Weird date/time. Docs: https://dateparser.readthedocs.io/en/latest/", mtype="groupchat")
                return
            else:
                date = date.replace(microsecond=0)

            seconds = (date - now).total_seconds()

            if seconds < 0:
                self.send_message(mto=msg['from'].bare, mbody="Error. Can't remind you in the past (%s)." % date.isoformat(), mtype="groupchat")
                return
            elif seconds > max_seconds:
                self.send_message(mto=msg['from'].bare, mbody="Error. Please set reminder to less than 1 week (%s)." % date.isoformat(), mtype="groupchat")
                return

            print("Reminder in {} sec at {}.".format(seconds, date.isoformat()))
            self.send_message(mto=msg['from'].bare, mbody="Reminder set at %s" % date.isoformat(), mtype="groupchat")
            Timer(seconds, self.send_message, kwargs={"mto": msg['from'].bare, "mbody": response, "mtype": "groupchat"}).start()

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
    parser.add_argument("-c", "--config", help="alternative config path", default="mybot.ini")

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel, format='%(levelname)-8s %(message)s')

    config = configparser.ConfigParser()
    config.read(args.config)
    jid = config["mybot"]["jid"]

    password = getpass.getpass("Password: ")

    processes = []
    for section in [section for section in config.sections() if section != "mybot"]:
        room = section
        nick = config[section]["nick"]
        resource = config[section]["resource"]
        xmpp = MyBot("{}/{}".format(jid, resource), password, room, nick)
        process = MyBotProcess(xmpp)
        process.start()
        processes.append(process)

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt as e:
        pass
