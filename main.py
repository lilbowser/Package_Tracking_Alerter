"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Consider using http://curiosityhealsthecat.blogspot.com/2013/07/using-python-decorators-for-registering_8614.html
for callback functions

"""

import re
import time
import logging

# import yaml
# from slacker import Slacker
# from slacksocket import SlackSocket
from SlackBot import SlackInterface
import utils
import datetime
from GmailScanner import Gmail
from Tracking.Packages import Packages
from Tracking.Packages import Package  # Only here for type hinting.
import Tracking.Tracker as Tracker

logging.basicConfig(level=logging.WARNING,
                    format="[%(asctime)s] %(name)s: %(funcName)s:%(lineno)d %(levelname)s:-8s %(message)s",
                    datefmt='%m-%d %H:%M:%S',
                    filename='Package_Tracker.log',
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
# formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
formatter = logging.Formatter("[%(asctime)s] %(name)s: %(funcName)s:%(lineno)d %(levelname)s:-8s %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


config = utils.load_api_config('secrets.yaml')

slack = SlackInterface(config['slack']['key'])  # Type: SlackInterface
start_time = datetime.datetime.now()


def new_email_received(_emails):

    for email in _emails:
        carrier, tracking_number = Tracker.search_for_tracking_number(email['body'])
        if tracking_number is not None:
            # Found a tracking number, attempt to add it to the packages list.
            success = packages.add_package(carrier, tracking_number, name=email["from_address"],
                                           subject=email['subject'])
            if success:
                slack.post_message('#general', 'New tracking number detected: {} from {}'.format(
                    tracking_number, email['from_address']))


def new_tracking_event(package: Package):
    slack.post_message('#general', 'Package {} is now {} at {}'.format(package.package_name,
                                                                       package.info.events[-1].detail,
                                                                       package.info.events[-1].location))
    package.last_message_sent = datetime.datetime.now()


def new_email_address_event(package: Package):
    slack.post_message('#general', 'Package {} is now {} at {}'.format(package.email_address,
                                                                       package.info.events[-1].detail,
                                                                       package.info.events[-1].location))


def respond_to_messages():
    events = slack.get_events()

    for event in events:
        if event.event['type'] == 'message':
            text = event.event['text'].strip()
            if text.lower() == 'time':
                slack.post_message(event.event['channel'], "The current time is {}".format(datetime.datetime.now()))

            elif text.lower() == 'uptime':
                uptime = datetime.datetime.now() - start_time
                slack.post_message(event.event['channel'], "I have been running for {}".format(uptime))

            elif text.lower() == 'list packages':
                slack.post_message(event.event['channel'], "Here is a list of all packages on file:".format())
                for package in packages.packages:
                    slack.post_message(event.event['channel'], "{}".format(package))

            elif text.lower().startswith("status "):
                tnumber = text.replace("status ", "")
                found = False

                for package in packages.packages:
                    if str(package.number) == tnumber:
                        found = True  # Print details
                        slack.post_message(
                            '#general', 'Package {} is now {} at {}'.format(package.package_name,
                                                                            package.info.events[-1].detail,
                                                                            package.info.events[-1].location))

                if not found:
                    slack.post_message(event.event['channel'], "Tracking Number {} not found".format(tnumber))

            elif text.lower().startswith("rename last "):
                name = text.replace("rename last ", "")

                package = packages.most_recent_updated_package()
                slack.post_message(event.event['channel'], "Name updated from {} to {} ".format(package, name))
                package.custom_name = name

            elif text.lower().startswith("rename "):
                # rename number name is here
                strings = text.split()

                package = packages.search_for_package(strings[1])
                if package is not None and len(strings) > 2:
                    new_name = ""
                    for name_part in strings[2:]:
                        new_name += " " + name_part
                    if new_name != "":
                        package.custom_name = new_name.strip()

            elif text.lower().startswith("add "):
                # add Number name
                strings = text.split()

                carrier, number = Tracker.search_for_tracking_number(strings[1])
                new_name = "custom_Add"
                if len(strings) > 2:
                    new_name = ""
                    for name_part in strings[2:]:
                        new_name += " " + name_part
                    if new_name != "":
                        new_name = new_name.strip()
                packages.add_package(carrier, number, new_name)
                packages.update_tracking()


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

        respond_to_messages()

        time.sleep(1)
        count += 1


