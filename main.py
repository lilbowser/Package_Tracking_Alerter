"""
MIT License
Copyright (c) 2016 Ashley Goldfarb
"""


from GmailScanner import Gmail
from Tracking.Packages import Packages
from Tracking.Packages import Package  # Only here for type hinting.

from slacker import Slacker
import yaml
import re
import time


def load_config(config_file_name):
    with open(config_file_name) as _config:
        return yaml.load(_config)["api_keys"]

config = load_config('secrets.yaml')
slack = Slacker(config['slack']['key'])


def new_email_received(_emails):

    for email in _emails:
        carrier, tracking_number = search_for_tracking(email['body'])
        if tracking_number is not None:
            # Found a tracking number, attempt to add it to the packages list.
            success = packages.add_package(carrier, tracking_number, name=email["from_address"])
            if success:
                slack.chat.post_message('#general', 'New tracking number detected: {} from {}'.format(
                    tracking_number, email['from_address']))


def new_tracking_event(package: Package):
    slack.chat.post_message('#general', 'Package {} is now {} at {}'.format(package.name, package.info.events[-1].detail,
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


if __name__ == '__main__':
    gmail = Gmail()
    packages = Packages()

    gmail.new_email_callback = new_email_received
    packages.define_callback(new_tracking_event)

    while True:
        gmail.get_recent_messages()
        packages.update_tracking()

        print("waiting 10 seconds")
        time.sleep(10)

