from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/question/(?P<question_id>\d+)/$', consumers.QuestionConsumer.as_asgi()),
    re_path(r'ws/likes/(?P<question_id>\d+)/$', consumers.LikesConsumer.as_asgi()),
]