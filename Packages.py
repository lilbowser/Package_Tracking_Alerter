"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Classes to store Package Data
"""

import datetime
import dill
from tracking import Tracker


class Package:

    tracker = Tracker()

    def __init__(self, carrier, tracking_number, name):

        self.name = name
        self.carrier = carrier
        self.number = tracking_number
        self.status = None
        self.last_update_time = datetime.datetime.min

    def get_tracking_data(self):
        self.tracker.get_tracking_data(self.number)


class Packages:

    def __init__(self):
        self.packages = [] # type: List[Package]



    def add_package(self, name, service, tracking_number):

        duplicate = False
        for package in self.packages:
            if package.number == tracking_number:
                duplicate = True

        if not duplicate:
            self.packages.append(Package(service, tracking_number, name))






if __name__ == '__main__':

    packages = Packages()
    packages.add_package("usps", "12836933")

    print(dill.pickles(packages))