"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Slacker Test Code

"""

from slacker import Slacker
from slacksocket import SlackSocket

import utils

import datetime


class SlackInterface:

    def __init__(self, api_token, default_name="packages", default_normal_user=False,
                 default_icon="http://i.imgur.com/MFB7wOd.png"):
        self.api_token = api_token
        self.slack = Slacker(api_token)
        self.slack_socket = SlackSocket(api_token)
        self.default_name = default_name
        self.default_normal_user = default_normal_user
        self.default_icon = default_icon
        self.connection_start = datetime.datetime.now()



    @property
    def chat(self):
        return self.slack.chat


    #region Slacker_Methods
    """ --- Slacker Methods --- """

    def post_message(self, channel="#general", body=None, username=None, icon_url=None):
        """
        Posts a message to slack.
        :param channel: The channel the message is to be posted to. (Opt)(Default: #general)
        :type channel: str
        :param body: The body of the message
        :type body: str
        :param username: Which username should the message be posted as. (Opt)
        :type username: Union[Union[Union[None, None], None], None]
        :param icon_url: Which icon whould the user have. (Opt)
        :type icon_url: Union[Union[Union[None, None], None], None]
        :return:
        :rtype: None
        """

        if username is None:
            username = self.default_name
        if icon_url is None:
            icon_url = self.default_icon

        if body is not None:
            self.slack.chat.post_message(channel, body, username=username, as_user=False,
                                         icon_url=icon_url)

    #endregion

    """ --- RTM Methods --- """
    def get_event(self):
        """
        Gets the next new event from the RTM api
        :return:
        :rtype:
        """
        try:
            e = self.slack_socket._eventq.pop(0)
            return e
        except IndexError:
            return None


    def get_events(self):
        """
        Gets all new events from the RTM api
        :return:
        :rtype:
        """
        ret = []
        while True:
            rsp = self.get_event()
            if rsp is not None:
                ret.append(rsp)
            else:
                break
        return ret

    #
    # def poll_slack(self):
    #     """
    #     Retrieves all new slack events and acts upon any relevant events.
    #     :return:
    #     :rtype:
    #     """
    #     for event in self.get_events():
    #         # print(event.json)
    #
    #         if event.event['type'] == 'message':
    #             try:
    #                 print("{} said {}".format(event.event['user'], event.event['text']))
    #             except KeyError:
    #                 pass
    #             text = event.event['text'].lower().strip()
    #             if text == 'time':
    #                 self.post_message(event.event['channel'], "The current time is {}".format(datetime.datetime.now()))
    #
    #             elif text == 'uptime':
    #                 uptime = datetime.datetime.now() - self.connection_start
    #                 self.post_message(event.event['channel'], "I have been running for {}".format(uptime))
    #             # else:
    #             #     for func in self.bot_listening_functions:


    def get_messages(self):
        ret = []
        for event in self.get_events():
            if event.event['type'] == 'message':
                try:
                    print("{} said {}".format(event.event['user'], event.event['text']))
                except KeyError:
                    pass
                text = event.event['text'].lower().strip()
                ret.append(event.event)
        return ret


    """ --- Listening Methods --- """








if __name__ == '__main__':

    config = utils.load_api_config('secrets.yaml')
    # slack = Slacker(config['slack']['key'])
    slack = SlackInterface(config['slack']['key'])

    # Send a message to #general channel
    # slack.chat.post_message('#general', 'Hello fellow slackers! The current time is {}.'.format(datetime.datetime.now()))
    slack.post_message(body='Hello fellow slackers! The current time is {}.'.format(datetime.datetime.now()))

    # Get users list
    # response = slack.users.list()
    # users = response.body['members']
    # print(users)
    # Upload a file
    # slack.files.upload('hello.txt')
