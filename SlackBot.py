"""
MIT License
Copyright (c) 2016 Ashley Goldfarb

Slacker Test Code
"""

from slacker import Slacker

slack = Slacker('xoxp-64732089472-64729067860-64686766979-5df7efceba')

# Send a message to #general channel
slack.chat.post_message('#general', 'Hello fellow slackers!')

# Get users list
response = slack.users.list()
users = response.body['members']
print(users)
# Upload a file
# slack.files.upload('hello.txt')