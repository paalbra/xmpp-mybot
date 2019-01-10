#!/usr/bin/python
# coding: utf-8
import datetime
import difflib
import json
import logging
import re
import urllib.request


def get_close_names(name, names):
    # Exact match
    if name in names:
        return [name]

    # Partial exact matches
    possible_matches = []
    for n in names:
        if re.search(name, n, re.IGNORECASE):
            possible_matches.append(n)
    if possible_matches:
        return possible_matches

    # difflib matches
    possible_matches = difflib.get_close_matches(name, names, cutoff=0.4)
    if possible_matches:
        return possible_matches

    return None


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
            dinners.append("{}: {}.".format(_type, name))

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


def get_restaurant_names(name):
    restaurants = get_restaurants()
    restaurant_names = [r["name"] for r in restaurants]
    close_restaurant_names = get_close_names(name, restaurant_names)

    return close_restaurant_names


def get_restaurants():
    url = "https://sio.no/v1/open/restaurants/"
    content = urllib.request.urlopen(url).read()
    restaurants = json.loads(content)
    logging.debug("Found {} restaurants".format(len(restaurants)))
    return restaurants
