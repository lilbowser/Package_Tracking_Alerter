import datetime
import logging
import requests
import yaml
import time
import re

import xml_dict
from Tracking.Carriers.BaseInterface import BaseInterface
from Tracking.errors import *
from Tracking.TrackingData import TrackingInfo
from xml_dict import xml_to_dict

# logger = logging.getLogger('USPS_Interface')


class USPSInterface(BaseInterface):
    """
    https://www.usps.com/business/web-tools-apis/track-and-confirm-api.htm

    Stores the following additional parameters in TrackingInfo:
     service
     expected_delivery_date (Optional)
     predicted_delivery_date (Optional)
     status_summary (Optional)

    """
    SHORT_NAME = 'usps'
    LONG_NAME = 'U.S. Postal Service'

    _api_urls = {
        'secure_test': 'https://secure.shippingapis.com/ShippingAPITest.dll?' \
            'API=TrackV2&XML=',
        'test':        'http://testing.shippingapis.com/ShippingAPITest.dll?' \
            'API=TrackV2&XML=',
        'production':  'http://production.shippingapis.com/ShippingAPI.dll?' \
            'API=TrackV2&XML=',
        'secure':      'https://secure.shippingapis.com/ShippingAPI.dll?' \
            'API=TrackV2&XML=',
        'local':       'http://127.0.0.1:5000/rev1?',
    }
    # _service_types = {
    #     'EA': 'Express Mail',
    #     'EC': 'Express Mail International',
    #     'CP': 'Priority Mail International',
    #     'RA': 'Registered Mail Domestic',
    #     'RF': 'Registered Mail Foreign',
    #     # 'EJ': 'something?',
    # }
    _url_template = 'https://tools.usps.com/go/TrackConfirmAction.action?tLabels={tracking_number}'
    # _request_xml = '<TrackFieldRequest USERID="{userid}">' \
    #     '<TrackID ID="{tracking_number}"/></TrackFieldRequest>'

    _request_xml = '<TrackFieldRequest USERID="{userid}">' \
                             '<Revision>1</Revision>' \
                             '<ClientIp>127.0.0.1</ClientIp>' \
                             '<SourceId>John Doe</SourceId>' \
                             '<TrackID ID="{tracking_number}"></TrackID>' \
                             '</TrackFieldRequest>'

    def __init__(self, config):
        BaseInterface.__init__(self, config)
        self._log = logging.getLogger(self.__class__.__name__)

    def __str__(self):
        return self.SHORT_NAME

    # @BaseInterface.require_valid_tracking_number
    def track(self, tracking_number):
        resp = self._send_request(tracking_number)
        return self._parse_response(resp, tracking_number)

    def identify(self, tracking_number):
        """
        Returns true if tracking number belongs to this interface
        :param tracking_number:
        :type tracking_number:
        :return:
        :rtype:
        """
        # #
        # return {
        #     13: lambda tn: \
        #         tn[0:2].isalpha() and tn[2:9].isdigit() and tn[11:13].isalpha(),
        #     20: lambda tn: tn.isdigit() and tn.startswith('0'),
        #     22: lambda tn: tn.isdigit(),
        #     30: lambda tn: tn.isdigit(),
        # }.get(len(tracking_number), lambda tn: False)(tracking_number)
        carrier, tnum = self.search_for_tracking(tracking_number)
        if tnum is not None:
            if self.verify_tracking_number(tracking_number): # TODO: Consider verifying using the returned tnumber
                return True
        return False


    def search_for_tracking(self, content):
        """
        Find tracking numbers in text
        :param content:
        :type content:
        :return: carrier_id, tracking_number
        :rtype:
        """
        # USPS
        search = re.search(r"((?:92|93|94|95)(?:\d{20}|\d{24}))\b", content)
        if search is not None:
            # print("Found tracking number: " + search.groups()[0])
            return "usps", search.groups()[0]
        else:
            return None, None


    def verify_tracking_number(self, tracking_number):
        """
        Uses the MOD 10 check from page 42 of USPS_PUB199IMPBImpGuide.pdf
        Works on 22-26 digit USPS Tracking numbers. Does not yet work on international tracking numbers.
        :param tracking_number: the tracking number to verify
        :type tracking_number: str
        :return: Is tracking number valid
        :rtype: bool
        """

        # USPS Check
        try:
            check_digit = int(tracking_number[-1])

            numbers = []
            for letter in tracking_number:
                numbers.append(int(letter))
            numbers.reverse()
        except ValueError:
            # If the tracking number has letters in it
            return False

        sum1 = 0
        for number in numbers[1::2]:
            sum1 += number

        sum1 *= 3
        sum2 = 0
        for number in numbers[2::2]:
            sum2 += number

        final_sum = sum1 + sum2
        computed_check_digit = 0
        while (final_sum + computed_check_digit) % 10 != 0:
            computed_check_digit += 1
            mod = (final_sum + computed_check_digit) % 10
            # if mod == 0:
            #     print("Incrementing Computed Check digit to {}. Mod is 0! Found check digit.".format(
            #         computed_check_digit))
            # else:
            #     print("Incrementing Computed Check digit to {}. Mod is {}! Continuing search.".format(
            #         computed_check_digit, mod))

        if check_digit == computed_check_digit:
            # print("Check Successful")
            return True
        else:
            # print("Check Failed. Expected {}, got {}".format(check_digit, computed_check_digit))
            return False


    def is_delivered(self, tracking_number, tracking_info=None):
        # TODO: This is broken
        if tracking_info is None:
            tracking_info = self.track(tracking_number)
        return tracking_info.status.lower().startswith('delivered')

    def _build_request(self, tracking_number):
        return self._request_xml.format(
            userid=self._config['userid'],
            tracking_number=tracking_number)

    def _parse_response(self, raw, tracking_number):
        rsp = xml_to_dict(raw)
        # this is a system error
        if 'Error' in rsp:
            error = rsp['Error']['Description']
            raise TrackingApiFailure(error)

        # this is a result with an error, like "no such package"
        try:
            if 'Error' in rsp['TrackResponse']['TrackInfo']:
                error = rsp['TrackResponse']['TrackInfo']['Error']['Description']
                raise TrackingNumberFailure(error)
        except KeyError:
            raise TrackingApiFailure(rsp)

        # make sure the events list is a list
        try:
            events = rsp['TrackResponse']['TrackInfo']['TrackDetail']
        except KeyError:
            events = []
        else:
            if type(events) != list:
                events = [events]
        summary = rsp['TrackResponse']['TrackInfo']['TrackSummary']

        # USPS doesn't return this, so we work it out from the tracking number
        if 'Class' in rsp['TrackResponse']['TrackInfo']:
            service_description = rsp['TrackResponse']['TrackInfo']['Class']  # "Not_Implemented" #"#self._service_types.get(tracking_number[0:2], 'USPS')
        else:
            service_description = None

        trackinfo = TrackingInfo(
            tracking_number = tracking_number,
            service         = service_description,
        )

        if 'ExpectedDeliveryDate' in rsp['TrackResponse']['TrackInfo']:
            trackinfo['expected_delivery_date'] = rsp['TrackResponse']['TrackInfo']['ExpectedDeliveryDate'] # TODO: Convert to datetime obj

        if 'PredictedDeliveryDate' in rsp['TrackResponse']['TrackInfo']:
            trackinfo['predicted_delivery_date'] = rsp['TrackResponse']['TrackInfo'][
                'PredictedDeliveryDate']  # TODO: Convert to datetime obj

        if 'StatusSummary' in rsp['TrackResponse']['TrackInfo']:
            trackinfo['status_summary'] = rsp['TrackResponse']['TrackInfo']['StatusSummary']

        # add the summary event, USPS doesn't duplicate it in the event log,
        # but we want it there
        trackinfo.create_event(
            location=self._getTrackingLocation(summary),
            timestamp=self._getTrackingDate(summary),
            detail=summary['Event'])

        for e in events:
            trackinfo.create_event(
                location = self._getTrackingLocation(e),
                timestamp= self._getTrackingDate(e),
                detail   = e['Event'],
            )

        trackinfo.is_delivered = self.is_delivered(None, trackinfo)
        if trackinfo.is_delivered:
            trackinfo.delivery_date = trackinfo.last_update

        return trackinfo

    def _send_request(self, tracking_number):
        url = self._api_urls[self._config['server_mode']] + \
            self._build_request(tracking_number)
        try:
            response = requests.get(url).text
        except requests.exceptions.ConnectionError as err:
            self._log.warning("Connection Error. Retrying in 1 second. {}".format(err))
            time.sleep(1)
            return self._send_request(tracking_number)
        return response

    def _getTrackingDate(self, node):
        """Returns a datetime object for the given node's
        <EventTime> and <EventDate> elements"""
        try:
            date = datetime.datetime.strptime(node['EventDate'], '%B %d, %Y').date()
        except ValueError:
            date = datetime.datetime.now() - datetime.timedelta(7)
        time = datetime.datetime.strptime(node['EventTime'], '%I:%M %p').time() \
            if node['EventTime'] else datetime.time(0, 0, 0)
        return datetime.datetime.combine(date, time)

    def _getTrackingLocation(self, node):
        """Returns a location given a node that has
            EventCity, EventState, EventCountry elements"""
        return ','.join(node[key] for key in ('Event'+i for i in ['City', 'State', 'Country']) \
                if node[key]) or \
            'USA'



class USPSTracker:

    usps_api_url = "http://production.shippingapis.com/ShippingAPI.dll?API=TrackV2&XML="
    usps_request_template = \
        '<TrackRequest USERID="{user_id}"><TrackID ID="{tracking_number}"></TrackID></TrackRequest>'

    usps_tracking_template = '<TrackFieldRequest USERID="{user_id}">' \
                             '<Revision>1</Revision>' \
                             '<ClientIp>127.0.0.1</ClientIp>' \
                             '<SourceId>John Doe</SourceId>' \
                             '<TrackID ID="{tracking_number}"></TrackID>' \
                             '</TrackFieldRequest>'

    def __init__(self, config_file="secrets.yaml"):
        self.config = self.load_config(config_file)["api_keys"]

    def load_config(self, config_file_name):
        with open(config_file_name) as config:
            return yaml.load(config)

    def get_tracking_data(self, tracking_number):
        request_url = self.usps_api_url + self.usps_tracking_template.format(user_id=self.config['usps']['key'],
                                                                            tracking_number=tracking_number)
        xml_response = requests.get(request_url).text
        tracking_dict = xml_dict.xml_to_dict(xml_response)

        if 'Error' in tracking_dict['TrackResponse']['TrackInfo']:
            error = tracking_dict['TrackResponse']['TrackInfo']['Error']['Description']

            print("Tracking Error on {tracking_number}: {error}".format(tracking_number=tracking_number, error=error))
        else:
            try:
                # tracking_dict['TrackResponse']['TrackInfo']['PredictedDeliveryDate']
                print("Package {tracking_number} is {status}. Expected Delivery on {expected}. Predicted Delivery on {predicted}".format(
                    tracking_number=tracking_number, status=tracking_dict['TrackResponse']['TrackInfo']['Status'],
                    expected=tracking_dict['TrackResponse']['TrackInfo']['ExpectedDeliveryDate'],
                    predicted=""
                ))
            except KeyError:
                print("Unknown Tracking Error on {}".format(tracking_number))

        print("")