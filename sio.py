#!/usr/bin/python
# coding: utf-8
import datetime
import json
import logging
import urllib


def get_menu(name="Ole-Johan spiseri"):
    restaurant = get_restaurant(name)

    if not restaurant:
        # No such restaurant
        # TODO: Raise error?
        return None
    elif "menu" not in restaurant:
        # Restaurant without menu
        return None

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    filtered_menu = [m for m in restaurant["menu"] if m["date"] == today]

    logging.debug("Found {} menu in restaurant ({})".format(len(filtered_menu), name))

    if len(filtered_menu) == 1:
        # Found todays menu
        dinners = []
        for dinner in filtered_menu[0]["dinner"]:
            _type = dinner["type"].strip(" .").upper()
            name = dinner["name"].strip(" .")
            dinners.append(u"{}: {}.".format(_type, name))

        menu_string = " ".join(dinners)

        return menu_string
    elif len(filtered_menu) > 1:
        # Is this possible?
        return None
    else:
        # No menu for today
        return None


def get_restaurant(name):
    restaurants = get_restaurants()
    filtered_restaurants = [r for r in restaurants if r["name"] == name]

    logging.debug("Found {} restaurants from name ({})".format(len(filtered_restaurants), name))

    if len(filtered_restaurants) == 1:
        return filtered_restaurants[0]
    elif len(filtered_restaurants) > 1:
        # TODO: Handle?
        return None
    else:
        # TODO: Handle?
        return None


def get_restaurants():
    url = "https://sio.no/v1/open/restaurants/"
    content = urllib.urlopen(url).read()
    restaurants = json.loads(content)
    logging.debug("Found {} restaurants".format(len(restaurants)))
    return restaurants
