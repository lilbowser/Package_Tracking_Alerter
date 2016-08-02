"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Code for scanning new emails in gmail account. Requires a client secret in client_secret.json from google to operate.
"""
import base64
import email
import os
import re

import httplib2
import oauth2client
from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools

from Tracking.Packages import Packages

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_bodies(payload):

    bodies = []
    if payload["mimeType"].startswith("multipart"):
        for part in payload["parts"]:
            new_body = get_bodies(part)
            if new_body is not None:
                bodies.extend(new_body)
        return bodies

    elif payload["mimeType"].startswith("text"):
        return [payload["body"]["data"]]

    else:
        print("Unknown mimeType: " + payload["mimeType"])
        return None


def unpack_body(_email):
    body_list = unpack_body_worker(_email)
    ret_body = ""
    for body in body_list:
        ret_body += (" " + body)

    return ret_body


def unpack_body_worker(_email):

    bodies = []
    if _email.is_multipart():
        for part in _email.get_payload():
            new_body = unpack_body_worker(part)
            if new_body is not None:
                bodies.extend(new_body)
        return bodies

    else:
        return [_email.get_payload()]

    #
    # if _email.is_multipart():
    #     p_email['body'] = ""
    #     for part in _email.get_payload():
    #         p_email['body'] += (" " + part.get_payload())
    # else:
    #     p_email['body'] = _email.get_payload()


def decode_international_header(_header_string):

    if _header_string is not None:
        decoded_subjects = email.header.decode_header(_header_string)

        tmp_subject = ""
        for decoded_subject in decoded_subjects:

            if decoded_subject[1] is not None:
                tmp_subject += decoded_subject[0].decode(decoded_subject[1])
            else:
                if isinstance(decoded_subject[0], bytes):
                    tmp_subject += decoded_subject[0].decode()
                else:
                    tmp_subject += decoded_subject[0]
        return tmp_subject
    else:
        return None

def parse_email_address(_address):
    """

    :param _address:
    :type _address:
    :return: (Sender Name, Sender Address)
    :rtype: (str, str)
    """
    decoded_address = decode_international_header(_address)
    search = re.search(r"(.*) <(.*)>", decoded_address)
    if search is not None:
        return search.groups()
    else:
        return (None, decoded_address)


def unpack_email(_email, _id):
    p_email = {}
    p_email['email_object'] = _email
    p_email['to'] = _email['to']
    p_email['from_name'], p_email['from_address'] = parse_email_address(_email['from'])
    p_email['subject'] = decode_international_header(_email['subject'])
    p_email['body'] = unpack_body(_email)
    p_email['id'] = _id

    return p_email


def get_mime_message(service, user_id, msg_id):
    """Get a Message and use it to create a MIME Message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The ID of the Message required.

    Returns:
      A MIME Message, consisting of data from Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id,
                                                 format='raw').execute()

        print('Message snippet: %s' % message['snippet'])

        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
        decoded_str = msg_str.decode('utf-8', errors='ignore')
        mime_msg = email.message_from_string(decoded_str)
        return mime_msg
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def search_for_tracking(content):
    """
    Searches for USPS, UPS, Fedex, EMS, and SAL Tracking numbers
    :param content: Content to search through
    :type content: str
    :return: (Shipping Service, Tracking Number)
    :rtype: (str, str)
    """

    # USPS
    search = re.search(r"((?:92|93|94|95)(?:\d{20}|\d{24}))\b", content)
    if search is not None:
        # print("Found tracking number: " + search.groups()[0])
        return ("usps", search.groups()[0])

    #  UPS
    search = re.search(r"\b(1Z ?[0-9A-Z]{3} ?[0-9A-Z]{3} ?[0-9A-Z]{2} ?[0-9A-Z]{4} ?[0-9A-Z]{3} ?[0-9A-Z])\b", content)
    if search is not None:
        return ("ups", search.groups()[0])

    #  Japan Post
    search = re.search(r"((?:[A-Z]|[a-z]){2}\d{9}JP)\b", content)
    if search is not None:
        return ("japan_post", search.groups()[0])

    #  if no match
    return (None, None)


def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    message_results = service.users().messages().list(userId="me", includeSpamTrash=False).execute()

    messages = []
    for message_id in message_results["messages"]:
        # message_response = service.users().messages().get(userId="me", id=message_id['id'], format="full").execute()

        mime_msg = get_mime_message(service, "me", message_id['id'])
        unpacked_msg = unpack_email(mime_msg, message_id['id'])
        messages.append(unpacked_msg)

    packages = Packages()
    for message in messages:
        service, trackingNum = search_for_tracking(message["body"])
        if service is not None:
            print("Found {} Tracking number {} in email: {} from {}".format(service, trackingNum, message["subject"], message["from_address"]) )
            packages.add_package(message["from_address"], service, trackingNum)

    for package in packages.packages:
        """type:  Package"""
        package.get_tracking_data()





    print("Done")


if __name__ == '__main__':
    main()