import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Question, Answer

class QuestionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.question_id = self.scope['url_route']['kwargs']['question_id']
        self.question_group_name = f'question_{self.question_id}'
        
        await self.channel_layer.group_add(
            self.question_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.question_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'new_answer':
            await self.channel_layer.group_send(
                self.question_group_name,
                {
                    'type': 'new_answer_message',
                    'answer': data['answer']
                }
            )

    async def new_answer_message(self, event):
        await self.send(text_data=json.dumps(event))

class LikesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.question_id = self.scope['url_route']['kwargs']['question_id']
        self.likes_group_name = f'likes_{self.question_id}'
        
        await self.channel_layer.group_add(
            self.likes_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.likes_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type in ['question_like', 'answer_like']:
            await self.channel_layer.group_send(
                self.likes_group_name,
                {
                    'type': 'like_update',
                    'data': data
                }
            )

    async def like_update(self, event):
        await self.send(text_data=json.dumps(event['data']))