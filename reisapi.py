#!/usr/bin/env python
#coding: utf-8
from pprint import pprint
import bs4
import datetime
import dateutil
import dateutil.relativedelta
import dateutil.parser
import json
import requests

def get_pretty_timedelta(timedelta):
    seconds = int(timedelta.total_seconds())
    hours, minutes, seconds = seconds / 3600, (seconds % 3600) / 60, seconds % 60
    if hours > 0:
        return "{}h {}m {}s".format(hours, minutes, seconds)
    elif minutes > 0:
        return "{}m {}s".format(minutes, seconds)
    else:
        return "{}s".format(seconds)

def get_departures():
    # Forskningsparken
    url = r"https://reisapi.ruter.no/StopVisit/GetDepartures/3010370"
    response = requests.get(url)
    departures = json.loads(response.text)

    platforms = {}

    for departure in departures:
        monitored = departure["MonitoredVehicleJourney"]["Monitored"]
        aimed_departure_time = departure["MonitoredVehicleJourney"]["MonitoredCall"]["AimedDepartureTime"]
        expected_departure_time = departure["MonitoredVehicleJourney"]["MonitoredCall"]["ExpectedDepartureTime"]
        departure_platform_name = departure["MonitoredVehicleJourney"]["MonitoredCall"]["DeparturePlatformName"]
        destination_name = departure["MonitoredVehicleJourney"]["DestinationName"]
        published_line_name = departure["MonitoredVehicleJourney"]["PublishedLineName"]

        if not monitored:
            # Skip vehicles that aren't monitored
            # Not monitored probably means that the OriginAimedDepartureTime is in the future?
            # Missing doc: http://reisapi.ruter.no/Help/ResourceModel?modelName=MonitoredVehicleJourney
            continue

        time_object = dateutil.parser.parse(expected_departure_time)
        relative_time = time_object - datetime.datetime.now(time_object.tzinfo)

        if relative_time > datetime.timedelta(minutes=20):
            # Skip departures in relatively distant future
            continue
        
        dep = "{} {} [{}]".format(published_line_name, destination_name, get_pretty_timedelta(relative_time))

        if departure_platform_name not in platforms:
            platforms[departure_platform_name] = [dep]
        else:
            platforms[departure_platform_name].append(dep)

    return platforms

if __name__ == "__main__":
    for k, v in get_pretty_departures().iteritems():
        s = "Platform {}: ".format(k)
        s += "; ".join(v)
        print s

