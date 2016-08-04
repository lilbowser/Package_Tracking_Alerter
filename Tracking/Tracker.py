"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Package Tracking Code
Based on https://github.com/aheadley/packagetrack/
"""

# import requests
import yaml

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

configuration = load_config("secrets.yaml")
register_carrier(USPSInterface, configuration['usps'])
# register_carrier(UPSInterface, config['ups'])
# register_carrier(FedExInterface, config['fedex'])

if __name__ == '__main__':
    # tracker = Tracker()
    # tracker.get_tracking_data("9361289673090100002806")

    print("Done")
