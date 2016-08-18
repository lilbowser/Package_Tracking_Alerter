"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Package Tracking Code
Based on https://github.com/aheadley/packagetrack/
"""

# import requests
import yaml
import re

# import xml_dict
# from Packages import Packages
from Tracking.errors import TrackingFailure, UnsupportedTrackingNumber, InvalidTrackingNumber, UnsupportedCarrier
from Tracking.Carriers.USPS import USPSInterface

__carriers = {}


def load_config(config_file_name):
    with open(config_file_name) as config:
        return yaml.load(config)["api_keys"]


def register_carrier(carrier_iface, config):
    """Register a carrier class, making it available to new Packages
    The new carrier instance will replace an older one with the same string
    representation
    """

    carrier = carrier_iface(config)
    __carriers[str(carrier)] = carrier
    return carrier


def identify_carrier(carrier_name):
    """
    Returns the carrier interface from the carrier identifier
    :param carrier_name: The carrier identifier
    :type carrier_name: str
    :return: The carrier interface
    :rtype: USPSInterface
    """
    try:
        return __carriers[carrier_name.lower()]
    except KeyError:
        raise UnsupportedCarrier(carrier_name)


def identify_tracking_number(tracking_number):
    """Return the carrier matching the givent tracking number, raises
    UnsupportedTrackingNumber if no match is found
    """

    try:
        return identify_smart_post_number(tracking_number)
    except (InvalidTrackingNumber, UnsupportedTrackingNumber):
        for carrier in __carriers.values():
            if carrier.identify(tracking_number):
                return carrier
        else:
            raise UnsupportedTrackingNumber(tracking_number)


def identify_smart_post_number(tracking_number):
    if len(tracking_number) == 22:
        for carrier in (carrier for carrier in __carriers.values() \
                if carrier.identify(tracking_number)):
            try:
                carrier.track(tracking_number)
            except TrackingFailure as err:
                continue
            else:
                return carrier
        else:
            raise UnsupportedTrackingNumber(tracking_number)
    else:
        raise InvalidTrackingNumber(tracking_number)


def search_for_tracking_number(content):
    """
    Searches for valid USPS, UPS, Fedex, EMS, and SAL Tracking numbers
    :param content: Content to search through
    :type content: str
    :return: (Shipping Service, Tracking Number) Returns (none, none) if no match is found..
    :rtype: (str, str)
    """
    for carrier in __carriers.values():
        carrier_id, tnum = carrier.search_for_tracking(content)  # carrier_id, tnum
        if tnum is not None:
            valid = carrier.verify_tracking_number(tnum)
            if valid:
                return carrier_id, tnum  # TODO: return actual carrier object, not carrier_ID

    return None, None

    #
    # # USPS
    # search = re.search(r"((?:92|93|94|95)(?:\d{20}|\d{24}))\b", content)
    # if search is not None:
    #     # print("Found tracking number: " + search.groups()[0])
    #     return "usps", search.groups()[0]
    #
    # # UPS
    # search = re.search(r"\b(1Z ?[0-9A-Z]{3} ?[0-9A-Z]{3} ?[0-9A-Z]{2} ?[0-9A-Z]{4} ?[0-9A-Z]{3} ?[0-9A-Z])\b",
    #                    content)
    # if search is not None:
    #     return "ups", search.groups()[0]
    #
    # # Japan Post
    # search = re.search(r"((?:[A-Z]|[a-z]){2}\d{9}JP)\b", content)
    # if search is not None:
    #     return "japan_post", search.groups()[0]
    #
    # # if no match
    # return None, None

configuration = load_config("secrets.yaml")
register_carrier(USPSInterface, configuration['usps'])
# register_carrier(UPSInterface, config['ups'])
# register_carrier(FedExInterface, config['fedex'])

if __name__ == '__main__':
    # tracker = Tracker()
    # tracker.get_tracking_data("9361289673090100002806")

    print("Done")
