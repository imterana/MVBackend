from urllib.parse import parse_qs

import redis
from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ValidationError

from ..models import Event


def get_event_by_uuid(uuid):
    try:
        event = Event.objects.filter(uuid=uuid).first()
    except ValidationError:
        event = None
    return event


def retrieve_event_id(query_string):
    params = parse_qs(query_string)
    event_id = params.get(b'event_id')
    if event_id is None or len(event_id) != 1:
        return None

    return event_id[0].decode('utf-8')


def add_to_list(listname, value):
    r = redis.Redis(
        host='redis',
        port=6379)
    r.rpush(listname, value)


def get_list(listname):
    r = redis.Redis(
        host='redis',
        port=6379)

    return r.lrange(listname, 0, r.llen(listname))


class MarkingConsumer(JsonWebsocketConsumer):
    messages = ['ready_to_mark', 'prepare_to_mark', 'confirm_marking', 'refuse_marking']

    def connect(self):
        event_id = retrieve_event_id(self.scope['query_string'])
        if event_id is None:
            self.send_json({"error": "No event id"}, close=True)
            return

        event = get_event_by_uuid(event_id)
        if event is None:
            self.send_json({"error": "Invalid event"})
            self.close()
            return

        user = self.scope['user']
        if user not in event.users.all():
            self.send_json({"error": "You are not in the event"}, close=True)
            return
        self.accept()

        async_to_sync(self.channel_layer.group_add)("event{}".format(event_id), self.channel_name)
        add_to_list("ready_to_mark", user.id)
        self.send_json({"result": 'ok', "marking_list": get_list("mark_me")})
        self.marking_list = get_list("mark_me")
        self.event = event


    def disconnect(self, close_code):
        pass

    def receive_json(self, content, **kwargs):
        print(content)
        if content["message"] in self.messages:
            getattr(self, content["message"])(content.get("params"))
        else:
            self.send_json({"error": "No message"})

    def mark_me(self, params):
        pass

    def prepare_to_mark(self, params):
        self.send_json({"result": "ok"})


class MarkMeConsumer(JsonWebsocketConsumer):
    def connect(self):
        print(self.scope)
        event_id = retrieve_event_id(self.scope['query_string'])
        if event_id is None:
            self.send_json({"error": "No event id"}, close=True)
            return

        event = get_event_by_uuid(event_id)
        if event is None:
            self.send_json({"error": "Invalid event"})
            self.close()
            return

        user = self.scope['user']
        if user not in event.users.all():
            self.send_json({"error": "You are not in the event"}, close=True)
            return

        async_to_sync(self.channel_layer.group_add)("event{}".format(event_id), self.channel_name)
        async_to_sync(self.channel_layer.group_add)("mark_me", self.channel_name)
        async_to_sync(self.channel_layer.group_send)(
            "event{}".format(event_id),
            {
                'type': 'chat_message',
                'message': "mark_me",
                "params": {"user_id": user.id}
            }
        )
        self.event = event
        self.accept()
