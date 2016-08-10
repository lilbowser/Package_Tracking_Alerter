"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Code for scanning new emails in gmail account. Requires a client secret in client_secret.json from google to operate.
"""
import base64
import email
import os
import re
import logging
import copy
import time

import httplib2
import oauth2client
from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools

# from Tracking.Packages import Packages


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

# logger = logging.getLogger('GMail')


class Gmail:
    """ A Class for interfacing with Gmail"""

    def __init__(self):
        """
        Constructor for Gmail
        Initilizes the conection to the Gmail servers.
        """

        self._log = logging.getLogger(self.__class__.__name__)

        self.credentials = self.get_credentials()
        self.http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=self.http)
        self.newest_history_id_retrieved = None

        self.email = []  # stores the last 100 downloaded emails.
        self._new_email = []
        self.new_email_callback = lambda x: None

    @property
    def new_email(self):
        return self._new_email

    @new_email.setter
    def new_email(self, value):
        self._new_email = value
        self.new_email_callback(self._new_email)

    def history_test(self):
        # message_ids = self.service.users().messages().list(userId="me", includeSpamTrash=False).execute()
        # message_response = self.service.users().messages().get(userId="me", id='1564d571a97815be', format="raw").execute()
        history = self.service.users().history().list(userId="me", startHistoryId='9945333').execute()
        message_ids = history['history']['messages']


    def get_recent_messages(self):
        filter_params = 'in: all -label:"Trash" -label:"Spam"'
        if self.newest_history_id_retrieved is None:
            # We have no record of the last message we have stored (this is probably the first run)
            # Preform a full sync

            if len(self.email) > 0:  # Sanity Check
                raise RuntimeError("No record of last history id, yet we have stored email!")

            message_ids = self.full_email_sync(number=50)['messages']
        else:
            try:
                message_ids, new_history_id = self.incremental_email_sync()
            except errors.HttpError:
                self._log.warning(
                    "Partial sync encountered a 404 error. The HistoryID may be out of date or invalid. \
                    Preforming full sync.")
                message_ids = self.full_email_sync()['messages']

            if message_ids is None:
                # no new emails to retrieve
                return False

        new_messages = []
        for message_id in message_ids:
            try:
                mime_msg, gmail_msg = self.get_mime_message(self.service, "me", message_id['id'])
            except TypeError as e:
                self._log.exception("Exception getting Messages. Forcing full sync")
                self.newest_history_id_retrieved = None
                return False

            unpacked_msg = self.unpack_email(mime_msg, gmail_msg, message_id['id'])
            new_messages.append(unpacked_msg)

        if len(new_messages) > 0:
            self.new_email = copy.deepcopy(new_messages)
            self.email = new_messages + self.email  # append new emails to the beginning of the list to preserve order

        try:
            self.newest_history_id_retrieved = new_history_id
        except NameError:
            self.newest_history_id_retrieved = self.email[0]['gmail_object']['historyId']

        return True


    def full_email_sync(self, number=100, call_count=0):
        """
        Preforms a full email sync and clears the email buffer if there are email present

        Returns:
            messages().list() response from google
        """

        if len(self.email) > 0:
            self.email = []
        try:
            response = self.service.users().messages().list(userId="me", maxResults=10, includeSpamTrash=False).execute()
        except httplib2.HttpLib2Error as e:

            if call_count < 5:
                new_count = call_count + 1
                self._log.exception("HttpLib2 Error. Retrying in {} seconds.".format(new_count))
                time.sleep(new_count)
                return self.full_email_sync(call_count=new_count)
            else:
                raise e

        except Exception as e:
            if call_count < 5:
                new_count = call_count + 1
                self._log.exception("Unknown Error. Retrying in {} seconds.".format(new_count))
                time.sleep(new_count)
                return self.incremental_email_sync(call_count=new_count)
            else:
                raise e

        messages = response['messages']
        need_more_emails = True
        while need_more_emails:
            if len(messages) >= number:
                break
            if 'nextPageToken' in response:
                try:
                    response = self.service.users().messages().list(userId="me", pageToken=response['nextPageToken'],
                                                                    maxResults=10, includeSpamTrash=False).execute()
                except httplib2.HttpLib2Error as e:

                    if call_count < 5:
                        new_count = call_count + 1
                        self._log.exception("HttpLib2 Error. Retrying in {} seconds.".format(new_count))
                        time.sleep(new_count)
                        return self.full_email_sync(call_count=new_count)
                    else:
                        raise e

                except Exception as e:
                    if call_count < 5:
                        new_count = call_count + 1
                        self._log.exception("Unknown Error. Retrying in {} seconds.".format(new_count))
                        time.sleep(new_count)
                        return self.incremental_email_sync(call_count=new_count)
                    else:
                        raise e

                messages.extend(response['messages'])
            else:
                break

        return {'messages': messages}


    def incremental_email_sync(self, call_count=0):
        """
        Preforms an incremental sync from the last history id recorded

        Returns: A list of message ids or None if there are no new messages

        """
        try:
            history = self.service.users().history().list(userId="me",
                                                          startHistoryId=self.newest_history_id_retrieved).execute()
        except httplib2.HttpLib2Error as e:

            if call_count < 5:
                new_count = call_count + 1
                self._log.exception("HttpLib2 Error. Retrying in {} seconds.".format(new_count))
                time.sleep(new_count)
                return self.incremental_email_sync(call_count=new_count)
            else:
                raise e

        except Exception as e:
            if call_count < 5:
                new_count = call_count + 1
                self._log.exception("Unknown Error. Retrying in {} seconds.".format(new_count))
                time.sleep(new_count)
                return self.incremental_email_sync(call_count=new_count)
            else:
                raise e

        if 'history' not in history:
            # No new messages to download
            self.newest_history_id_retrieved = history['historyId']
            return None, None

        message_ids = []
        for event in history['history']:
            if 'messagesAdded' in event:
                message_ids.append({'id': event['messagesAdded'][0]['message']['id']})
                if len(event['messagesAdded']) > 1:
                    print("History message has more than 1 entry!!! WAT???!!!")

        if len(message_ids) < 1:
            # No added messages were in the response.
            self.newest_history_id_retrieved = history['historyId']
            return None, None

        return message_ids, history['historyId']


    def get_mime_message(self, service, user_id, msg_id, count=0):
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

            return mime_msg, message
        except errors.HttpError as error:
            self._log.exception('An error occurred:')
            if count < 5:
                ncount = count + 1
                return self.get_mime_message(service, user_id, msg_id, ncount)
            else:
                self._log.critical("Exceeded max number of retries. Skipping message.")


    #region Gmail Interface Methods
    """ --- Gmail Interface Methods --- """
    @staticmethod
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

    #endregion

    #region Email Unpacking
    """ --- Gmail Email Depacking Methods --- """
    # def get_bodies(self, payload):
    #
    #     bodies = []
    #     if payload["mimeType"].startswith("multipart"):
    #         for part in payload["parts"]:
    #             new_body = self.get_bodies(part)
    #             if new_body is not None:
    #                 bodies.extend(new_body)
    #         return bodies
    #
    #     elif payload["mimeType"].startswith("text"):
    #         return [payload["body"]["data"]]
    #
    #     else:
    #         print("Unknown mimeType: " + payload["mimeType"])
    #         return None

    def unpack_body(self, _email):
        body_list = self.unpack_body_worker(_email)
        ret_body = ""
        for body in body_list:
            ret_body += (" " + body)

        return ret_body


    def unpack_body_worker(self, _email):

        bodies = []
        if _email.is_multipart():
            for part in _email.get_payload():
                new_body = self.unpack_body_worker(part)
                if new_body is not None:
                    bodies.extend(new_body)
            return bodies

        else:
            return [_email.get_payload()]


    def decode_international_header(self, _header_string):

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


    def parse_email_address(self, _address):
        """

        :param _address:
        :type _address:
        :return: (Sender Name, Sender Address)
        :rtype: (str, str)
        """
        decoded_address = self.decode_international_header(_address)
        search = re.search(r"(.*) <(.*)>", decoded_address)
        if search is not None:
            return search.groups()
        else:
            return (None, decoded_address)


    def unpack_email(self, _email, _gmail_obj, _id):
        p_email = {}
        p_email['email_object'] = _email
        p_email['gmail_object'] = _gmail_obj
        p_email['to'] = _email['to']
        p_email['from_name'], p_email['from_address'] = self.parse_email_address(_email['from'])
        p_email['subject'] = self.decode_international_header(_email['subject'])
        p_email['body'] = self.unpack_body(_email)
        p_email['id'] = _id

        return p_email

    #endregion

    ''' --- Search Code --- '''


def old_manual_method():
    pass
    # credentials = get_credentials()
    # http = credentials.authorize(httplib2.Http())
    # service = discovery.build('gmail', 'v1', http=http)
    #

    #
    # message_results = service.users().messages().list(userId="me", includeSpamTrash=False).execute()
    #
    # messages = []
    # for message_id in message_results["messages"]:
    #     # message_response = service.users().messages().get(userId="me", id=message_id['id'], format="full").execute()
    #
    #     mime_msg = get_mime_message(service, "me", message_id['id'])
    #     unpacked_msg = unpack_email(mime_msg, message_id['id'])
    #     messages.append(unpacked_msg)
    #
    # packages = Packages()
    # for message in messages:
    #     carrier, trackingNum = search_for_tracking(message["body"])
    #     if carrier is not None:
    #         print("Found {} Tracking number {} in email: {} from {}".format(carrier, trackingNum, message["subject"],
    #                                                                         message["from_address"]))
    #         packages.add_package(carrier, trackingNum, name=message["from_address"], )
    #
    # for package in packages.packages:
    #     """type:  Package"""
    #     package.get_tracking_data()


def test_callback(_email):
    print("{} New emails received".format(len(_email)))


def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    import time
    gmail_interface = Gmail()
    gmail_interface.new_email_callback = test_callback

    count = 100
    for i in range(count):
        success = gmail_interface.get_recent_messages()

        if success:
            print("New emails received")
        else:
            print("No new emails")
        print("delaying for 1 minute check for new emails")
        time.sleep(20)


    print("Done")


if __name__ == '__main__':
    main()