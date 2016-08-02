"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Classes to store Package Data
Based on https://github.com/aheadley/packagetrack/
"""

import datetime
import dill
# from Tracking import Tracker
import Tracking.Tracker as Tracker


class Package:

    # tracker = Tracker()

    def __init__(self, carrier, tracking_number, name=None):

        self.name = name
        self.carrier = Tracker.identify_carrier(carrier)  # type: Tracking.Carriers.BaseInterface.BaseInterface
        self.number = tracking_number
        self.info = None#TrackingInfo(tracking_number)
        # self.last_update_time = datetime.datetime.min

    def get_tracking_data(self):
        # self.carrier.get_tracking_data(self.number)
        self.info = self.carrier.track(self.number)


class Packages:

    def __init__(self):
        self.packages = []  # type: List[Package]

    def add_package(self, carrier, tracking_number, name=None):

        duplicate = False
        for package in self.packages:
            if package.number == tracking_number:
                duplicate = True

        if not duplicate:
            self.packages.append(Package(carrier, tracking_number, name))



if __name__ == '__main__':

    packages = Packages()
    packages.add_package("usps", "12836933")

    print(dill.pickles(packages))