import logging
import re

from Tracking.Carriers.USPS import USPSInterface


class JapanPostInterface(USPSInterface):

    SHORT_NAME = 'japan_post'
    LONG_NAME = 'Japan Post'

    def __init__(self, config):
        USPSInterface.__init__(self, config)
        self._log = logging.getLogger(self.__class__.__name__)

    def search_for_tracking(self, content):
        """
        Find tracking numbers in text
        :param content:
        :type content:
        :return: carrier_id, tracking_number
        :rtype:
        """
        # Japan Post
        search = re.search(r"((?:[A-Z]|[a-z]){2}\d{9}JP)\b", content)
        if search is not None:
            # print("Found tracking number: " + search.groups()[0])
            return "usps", search.groups()[0]
        else:
            return None, None


    def verify_tracking_number(self, tracking_number):
        """
        Not yet implemented. Currently always returns valid.
        :param tracking_number: the tracking number to verify
        :type tracking_number: str
        :return: Is tracking number valid
        :rtype: bool
        """

        # Japan Post Check
        # TODO: IMPLEMENT!
        return True

