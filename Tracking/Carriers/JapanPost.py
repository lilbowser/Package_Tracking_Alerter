import logging
import re

from Tracking.Carriers.USPS import USPSInterface


class JapanPostInterface(USPSInterface):
    """
    Utilises S10 tracking numbers
    """

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
            return "japan_post", search.groups()[0]
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
        try:
            id_number = tracking_number[2:11]
            check_digit = int(id_number[-1])

            sum = (int(id_number[0]) * 8) + \
                      (int(id_number[1]) * 6) + \
                      (int(id_number[2]) * 4) + \
                      (int(id_number[3]) * 2) + \
                      (int(id_number[4]) * 3) + \
                      (int(id_number[5]) * 5) + \
                      (int(id_number[6]) * 9) + \
                      (int(id_number[7]) * 7)
            calculated_check = 11 - (sum % 11)

            if calculated_check == 10:
                calculated_check = 0
            elif calculated_check == 11:
                calculated_check = 5

            if calculated_check == check_digit:
                return True
            else:
                return False
        except Exception:
            return False



