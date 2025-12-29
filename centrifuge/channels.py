import re
import time
import logging
from urllib.parse import urljoin

import jwt
from django.conf import settings
from cent import Client


logger = logging.getLogger(settings.PROJECT_NAME)


def connect_to_centrifuge():
    url = settings.CENTRIFUGE_HOST
    if url is None:
        return None
    if url[-1] != '/':
        url += '/'
    url += 'api'

    api_key = settings.CENTRIFUGE_API_KEY
    timeout = settings.CENTRIFUGE_TIMEOUT
    client = Client(url, api_key, timeout=timeout)
    return client


class BaseChannel(object):
    channel = None
    permissions = []

    SECRET = settings.CENTRIFUGE_SECRET
    EXPIRE = settings.CENTRIFUGE_TOKEN_EXPIRE

    def __init__(self, channel=None, centrifuge=None, channel_match=None):
        self.channel = channel
        self.centrifuge = centrifuge

    def get_channel(self, *args,  **kwargs):
        return self.channel

    def get_token(self, channel, user):
        expire = int(time.time()) + self.EXPIRE
        return jwt.encode({
            'sub': str(user.pk) if user else '',
            'channel': channel,
            'exp': expire
        }, self.SECRET, algorithm="HS256")

    def get_centrifuge(self):
        if self.centrifuge is None:
            self.centrifuge = connect_to_centrifuge()
        return self.centrifuge

    def publish(self, channel, data, msg_type='undefined'):
        ...

    @classmethod
    def get_channel_instance(cls, channel=None, centrifuge=None):
        match = re.match(cls.channel_pattern, channel)
        if match:
            return cls(channel, centrifuge, match)
        return None