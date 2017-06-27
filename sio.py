#!/usr/bin/python
#coding: utf-8
from bs4 import BeautifulSoup
import logging
import requests
import sys

def get_sio_dinner(restaurant_id = 284):
    url = "https://sio.no/mat-og-drikke/_window/mat+og+drikke+-+dagens+middag?s=%d" % restaurant_id
    content = requests.get(url).text
    soup = BeautifulSoup(content, "html.parser")

    output = ""
    for element in soup.find_all('h3'):
        output += "%s: " % element.text.upper()
        output += element.find_next_sibling().get_text().strip()
        if not output.endswith("."):
            output += ". "
        else:
            output += " "

    if len(output) > 1000:
        logging.warn("Very long output (%d) received from SiO: %s" % (len(output), output))
        return output[:1000] + " ... OUTPUT TRIMMED."
    else:
        return output

