#!/usr/bin/python
#coding: utf-8
from bs4 import BeautifulSoup
import logging
import sys

if sys.version_info < (3, 0):
    from urllib2 import urlopen
else:
    from urllib.request import urlopen

def get_sio_dinner(restaurant_id = 284):
    url = "https://www.sio.no/hjem/_window/forside+-+forsidebokser+(4+knapper)?s=%d" % restaurant_id
    content = urlopen(url).read()
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

