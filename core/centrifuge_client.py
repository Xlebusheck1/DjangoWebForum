import jwt
import time
from django.conf import settings

class CentrifugeClient:
    @staticmethod
    def generate_token(user_id, channel, exp=1800):
        expire = int(time.time()) + exp
        return jwt.encode({
            'sub': str(user_id),
            'channel': channel,
            'exp': expire
        }, settings.CENTRIFUGE_SECRET, algorithm="HS256")

    @staticmethod
    def generate_connection_token(user):
        expire = int(time.time()) + settings.CENTRIFUGE_TOKEN_EXPIRE
        return jwt.encode({
            'sub': str(user.id),
            'exp': expire
        }, settings.CENTRIFUGE_SECRET, algorithm="HS256")