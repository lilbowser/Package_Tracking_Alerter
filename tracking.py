"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Package Tracking Code
"""

import requests
import yaml
import xml.etree.ElementTree as ET
import xml_dict


class Tracker:

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


if __name__ == '__main__':
    tracker = Tracker()
    tracker.get_tracking_data("9361289673090100002806")

    print("Done")
