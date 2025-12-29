import jwt
import time
import json
from django.conf import settings
from cent import Client
import logging

logger = logging.getLogger(__name__)

class CentrifugeClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = None
        return cls._instance
    
    def get_client(self):
        if self.client is None:
            try:
                self.client = Client(
                    settings.CENTRIFUGE_HOST + '/api',
                    api_key=settings.CENTRIFUGE_API_KEY,
                    timeout=10
                )
            except Exception as e:
                logger.error(f"Failed to connect to Centrifugo: {e}")
                return None
        return self.client
    
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
    
    def publish_new_answer(self, question_id, answer_data):
        client = self.get_client()
        if client is None:
            return False
        
        try:
            channel = f"questions:question_{question_id}"
            client.publish(
                channel=channel,
                data={
                    "type": "new_answer",
                    "answer": answer_data
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish answer via Centrifugo: {e}")
            return False