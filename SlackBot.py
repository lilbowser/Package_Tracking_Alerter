"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Slacker Test Code
"""

from slacker import Slacker
import yaml
import datetime


def load_config(config_file_name):
    with open(config_file_name) as config:
        return yaml.load(config)["api_keys"]

if __name__ == '__main__':

    config = load_config('secrets.yaml')
    slack = Slacker(config['slack']['key'])

    # Send a message to #general channel
    slack.chat.post_message('#general', 'Hello fellow slackers! The current time is {}.'.format(datetime.datetime.now()))

    # Get users list
    response = slack.users.list()
    users = response.body['members']
    print(users)
    # Upload a file
    # slack.files.upload('hello.txt')
