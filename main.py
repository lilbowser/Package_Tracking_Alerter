"""
MIT License
Copyright (c) 2016 Ashley Goldfarb
"""

import re
import time
import datetime
import logging

import yaml
from slacker import Slacker
from slacksocket import SlackSocket
from SlackBot import SlackInterface
import utils

from GmailScanner import Gmail
from Tracking.Packages import Packages
from Tracking.Packages import Package  # Only here for type hinting.

logging.basicConfig(level=logging.WARNING,
                    format="[%(asctime)s] %(name)s: %(funcName)s:%(lineno)d %(levelname)s:-8s %(message)s",
                    datefmt='%m-%d %H:%M',
                    filename='Package_Tracker.log',
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
# formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
formatter = logging.Formatter("[%(asctime)s] %(name)s: %(funcName)s:%(lineno)d %(levelname)s:-8s %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


config = utils.load_api_config('secrets.yaml')

slack = SlackInterface(config['slack']['key'], )
slack_socket = SlackSocket(config['slack']['key'])

start_time = datetime.datetime.now()


def new_email_received(_emails):

    for email in _emails:
        carrier, tracking_number = search_for_tracking(email['body'])
        if tracking_number is not None:
            # Found a tracking number, attempt to add it to the packages list.
            success = packages.add_package(carrier, tracking_number, name=email["from_address"])
            if success:
                slack.post_message('#general', 'New tracking number detected: {} from {}'.format(
                    tracking_number, email['from_address']))


def new_tracking_event(package: Package):
    slack.post_message('#general', 'Package {} is now {} at {}'.format(package.package_name, package.info.events[-1].detail,
                                                                            package.info.events[-1].location))

def new_email_address_event(package: Package):
    slack.post_message('#general', 'Package {} is now {} at {}'.format(package.email_address, package.info.events[-1].detail,
                                                                            package.info.events[-1].location))

def search_for_tracking(content):  # TODO: Consider a more appropriate location for this.
    """
    Searches for USPS, UPS, Fedex, EMS, and SAL Tracking numbers
    :param content: Content to search through
    :type content: str
    :return: (Shipping Service, Tracking Number)
    :rtype: (str, str)
    """

    # USPS
    search = re.search(r"((?:92|93|94|95)(?:\d{20}|\d{24}))\b", content)
    if search is not None:
        # print("Found tracking number: " + search.groups()[0])
        return "usps", search.groups()[0]

    # UPS
    search = re.search(r"\b(1Z ?[0-9A-Z]{3} ?[0-9A-Z]{3} ?[0-9A-Z]{2} ?[0-9A-Z]{4} ?[0-9A-Z]{3} ?[0-9A-Z])\b",
                       content)
    if search is not None:
        return "ups", search.groups()[0]

    # Japan Post
    search = re.search(r"((?:[A-Z]|[a-z]){2}\d{9}JP)\b", content)
    if search is not None:
        return "japan_post", search.groups()[0]

    # if no match
    return None, None


def get_event():
    try:
        e = slack_socket._eventq.pop(0)
        return e
    except IndexError:
        return None


def get_events():
    ret = []
    while True:
        rsp = get_event()
        if rsp is not None:
            ret.append(rsp)
        else:
            break
    return ret

if __name__ == '__main__':
    gmail = Gmail()
    packages = Packages().load_from_pickle()

    gmail.new_email_callback = new_email_received
    packages.define_callbacks(new_tracking_event)
    count = 0
    while True:

        if count%10 == 0:
            gmail.get_recent_messages()
            packages.update_tracking()
            print("waiting 10 seconds")

        for event in get_events():
            # print(event.json)
            if event.event['type'] == 'message':
                try:
                    print("{} said {}".format(event.event['user'], event.event['text']))
                except KeyError:
                    pass
                if event.event['text'].lower() == 'time':
                    slack.post_message(event.event['channel'], "The current time is {}".format(datetime.datetime.now()))
                elif event.event['text'].lower() == 'uptime':
                    uptime = datetime.datetime.now() - start_time
                    slack.post_message(event.event['channel'], "I have been running for {}".format(uptime))



        time.sleep(1)
        count += 1


