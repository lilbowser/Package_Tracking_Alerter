"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Classes to store Package Data
Based on https://github.com/aheadley/packagetrack/
"""

# import datetime
import dill
import logging

import Tracking.Tracker as Tracker
from Tracking import errors
from Tracking.TrackingData import TrackingInfo
import utils
import datetime
config = utils.load_api_config("secrets.yaml")
undesirable_email_addresses = config['undesirable_email_addresses']


class Package:

    # tracker = Tracker()

    def __init__(self, carrier, tracking_number, email_address=None, email_subject=None):

        self._log = logging.getLogger(self.__class__.__name__)
        self.carrier = Tracker.identify_carrier(carrier)
        self.number = tracking_number

        self._info = TrackingInfo(None)  # self.carrier.track(self.number)  # type: TrackingInfo
        self.new_event_callback = lambda x: None
        self.new_email_address_callback = lambda x: None

        self._email_address = None
        self._undesirable_email_address = True
        self.custom_name = None

        self.email_address = email_address
        self.email_subject = email_subject

        self.last_message_sent = datetime.datetime.min

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

    @property
    def undesirable_email_address(self):
        return self._undesirable_email_address

    @undesirable_email_address.setter
    def undesirable_email_address(self, value):
        self._undesirable_email_address = value
        self.new_email_address_callback(value)  # TODO: We need to pass something more rational

    @property
    def email_address(self):
        return self._email_address

    @email_address.setter
    def email_address(self, value):

        if type(value) == str:
            undesirable_email_address = False
            if value in undesirable_email_addresses:
                undesirable_email_address = True

            self.undesirable_email_address = undesirable_email_address
            self._email_address = value


    @property
    def package_name(self):
        if self.custom_name is not None:
            name = "{} ({})".format(self.custom_name, self.number)
        elif self.email_subject is not None and self.email_address:
            name = "{} ({}) <{}>".format(self.email_subject, self.number, self.email_address)
        elif self.email_subject is not None:
            name = "{} ({})".format(self.email_subject, self.number)
        elif self.email_address is not None:
            name = "{} ({})".format(self.email_address, self.number)
        else:
            name = "{}".format(self.number)

        return name

    def __str__(self):
        return self.package_name


    def get_tracking_data(self):
        # self.carrier.get_tracking_data(self.number)
        updated = False
        try:
            new_info = self.carrier.track(self.number)
            if new_info != self.info:
                updated = True

            self.info = self.carrier.track(self.number)
            return updated
        except (errors.TrackingNetworkFailure, errors.TrackingApiFailure) as e:
            self._log.exception("Unable to get tracking information for {} using {}".format(self.number, self.carrier))
            return updated


class Packages:
    """
    Stores and works with all Package()'s that we are tracking.
    """
    def __init__(self):
        self.packages = []  # type: List[Package]
        self.new_event_callback = lambda x: None
        self.email_address_callback = lambda x: None
        self._log = logging.getLogger(self.__class__.__name__)


    def define_callbacks(self, event_callback_function, email_address_callback=(lambda x: None)):
        self.new_event_callback = event_callback_function
        self.email_address_callback = email_address_callback
        for package in self.packages:
            package.new_event_callback = event_callback_function
            package.new_email_address_callback = email_address_callback

    def add_package(self, carrier, tracking_number, name=None, subject=None):
        duplicate = False

        for package in self.packages:
            if package.number == tracking_number:
                duplicate = True
                if package.email_address != name:
                    if package.undesirable_email_address:
                        self._log.warning("Changed name from {} to {}".format(package.email_address, name))
                        package.email_address = name

        if not duplicate:
            new_package = Package(carrier, tracking_number, name, subject)
            new_package.new_event_callback = self.new_event_callback
            self.packages.append(new_package)
            return True
        else:
            return False

    def most_recent_updated_package(self):
        latest_time = datetime.datetime.min
        latest_msg = None
        for package in self.packages:
            if package.last_message_sent > latest_time:
                latest_msg = package
                latest_time = package.last_message_sent

        return latest_msg

    def search_for_package(self, search_term):

        carrier, tracking_number = Tracker.search_for_tracking_number(search_term)
        if tracking_number is not None:
            # the search term is a tracking number. Match using numbers
            for package in self.packages:
                if str(package.number) == tracking_number:
                    return package
        else:
            # The search term is something else.... Lets search everything?
            for package in self.packages:
                if search_term.lower() in str(package).lower():
                    return package

        return None

    def update_tracking(self):
        """
        Updates the tracking info of all packages.
        If a package gets updated, rePickle the class.
        :return:
        :rtype: None
        """
        need_to_pickle = False
        packages_ro_remove = []
        for package in self.packages:
            try:
                if package.get_tracking_data():
                    need_to_pickle = True
            except errors.TrackingNumberFailure as e:
                self._log.exception("Tracking Number Failure. Removing package {} from the system.".format(package))
                packages_ro_remove.append(package)

        for package in packages_ro_remove:
            self.packages.remove(package)

        if need_to_pickle:
            self.one_two_pickle_your_shoe()

    def one_two_pickle_your_shoe(self):
        """
        Serializes instance of Packages() to pickle file.
        :return:
        :rtype:
        """

        with open('package_data.pickle', 'wb') as file:
            dill.dump(self, file)

    @staticmethod
    def load_from_pickle():
        """
        Returns a new Packages() initialized from pickled data.
        If no pickled data exists, we return a newly initialized Packages().

        :return: A new initialized Packages()
        :rtype: Packages
        """
        try:
            with open('package_data.pickle', 'rb') as file:
                ret = dill.load(file)
                return ret
        except FileNotFoundError:
            return Packages()



if __name__ == '__main__':

    packages = Packages()
    packages.add_package("usps", "12836933")

    print(dill.pickles(packages))  # Test to ensure object is still picklable
