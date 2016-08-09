"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Slacker Test Code
"""

from slacker import Slacker
import utils

import datetime


class SlackInterface:

    def __init__(self, api_token, default_name="packages", default_normal_user=False,
                 default_icon="http://i.imgur.com/MFB7wOd.png"):
        self.api_token = api_token
        self.slack = Slacker(api_token)
        self.default_name = default_name
        self.default_normal_user = default_normal_user
        self.default_icon = default_icon

    @property
    def chat(self):
        return self.slack.chat

    def post_message(self, channel="#general", body=None, username=None, icon_url=None):
        if username is None:
            username = self.default_name
        if icon_url is None:
            icon_url = self.default_icon

        if body is not None:
            self.slack.chat.post_message(channel, body, username=username, as_user=False,
                                         icon_url=icon_url)




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
