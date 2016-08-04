"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Classes to store Package Data
Based on https://github.com/aheadley/packagetrack/
"""

# import datetime
import dill

import Tracking.Tracker as Tracker
from Tracking.TrackingData import TrackingInfo



class Package:

    # tracker = Tracker()

    def __init__(self, carrier, tracking_number, name=None):

        self.name = name
        self.carrier = Tracker.identify_carrier(carrier)
        self.number = tracking_number
        self._info = TrackingInfo(None)  # self.carrier.track(self.number)  # type: TrackingInfo
        self.new_event_callback = lambda x: None
        # self.last_update_time = datetime.datetime.min


    @property
    def info(self):
        """

        :return: tracking info
        :rtype: TrackingInfo
        """
        return self._info

    @info.setter
    def info(self, value):
        if self._info != value:
            self._info = value
            self.new_event_callback(self)


    def get_tracking_data(self):
        # self.carrier.get_tracking_data(self.number)
        self.info = self.carrier.track(self.number)


class Packages:

    def __init__(self):
        self.packages = []  # type: List[Package]
        self.new_event_callback = lambda x: None

    def define_callback(self, callback_function):
        self.new_event_callback = callback_function
        for package in self.packages:
            package.new_event_callback = callback_function

    def add_package(self, carrier, tracking_number, name=None):

        duplicate = False
        for package in self.packages:
            if package.number == tracking_number:
                duplicate = True

        if not duplicate:
            new_package = Package(carrier, tracking_number, name)
            new_package.new_event_callback = self.new_event_callback
            self.packages.append(new_package)
            return True
        else:
            return False

    def update_tracking(self):
        for package in self.packages:
            package.get_tracking_data()


if __name__ == '__main__':

    packages = Packages()
    packages.add_package("usps", "12836933")

    print(dill.pickles(packages))  # Test to ensure object is still picklable
