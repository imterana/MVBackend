from urllib.parse import parse_qs

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ValidationError

from .storage import storage
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


class MarkingConsumer(JsonWebsocketConsumer):
    messages = ['prepare_to_mark', 'confirm_marking', 'refuse_marking']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marking_list = set()
        self.event = None
        self.prepared_user_id = None

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

        marking_list = storage.get_list("mark_me_{}".format(event_id))
        self.marking_list = set(marking_list)
        self.event = event

        async_to_sync(self.channel_layer.group_add)("event{}".format(event_id), self.channel_name)
        storage.add_to_list("ready_to_mark_{}".format(event_id), user.id)
        print(list(self.marking_list))
        self.send_json({"result": 'ok', "marking_list": marking_list})

    def disconnect(self, close_code):
        if self.event is not None:
            async_to_sync(self.channel_layer.group_discard)("event_{}".format(self.event.uuid), self.channel_name)
            # TODO remove from redis

    def receive_json(self, content, **kwargs):
        print(content)
        if content["message"] in self.messages:
            getattr(self, content["message"])(content.get("params"))
        else:
            self.send_json({"error": "No message"})

    def add_user(self, params):
        user_id = params.get('user_id')
        if user_id is None:
            return
        print(user_id)
        self.marking_list.add(user_id)
        self.send_json({'message': 'user_joined', "params": {'user_id': user_id}})

    def remove_user(self, params):
        user_id = params.get('user_id')
        if user_id is None:
            return
        self.marking_list.remove(user_id)
        self.send_json({'message': 'user_left', "params": {'user_id': 1234}})

    def prepare_to_mark(self, params):
        user_id = params.get('user_id')
        if user_id is None or self.prepared_user_id is not None:
            self.send_json({"result": "denial"})
            return

        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'remove.user',
                "params": {"user_id": user_id}
            }
        )
        self.prepared_user_id = user_id
        self.send_json({"result": "ok"})

    def confirm_marking(self, params):
        user_id = params.get('user_id')
        if user_id is None or self.prepared_user_id != user_id:
            self.send_json({"result": "denial"})
            return

        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'marked',
                "params": {"user_id": user_id}
            }
        )

        self.prepared_user_id = None
        self.send_json({"result": "ok"})

    def marked(self, params):
        pass

    def refuse_marking(self, params):
        user_id = params.get('user_id')
        if user_id is None or self.prepared_user_id != user_id:
            return
        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'add.user',
                "params": {"user_id": self.prepared_user_id}
            }
        )
        self.prepared_user_id = None
        self.send_json({"result": "ok"})


class MarkMeConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = None

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

        self.event = event

        async_to_sync(self.channel_layer.group_add)("event_{}".format(event_id), self.channel_name)
        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(event_id),
            {
                'type': 'add.user',
                "params": {"user_id": user.id}
            }
        )
        print(user.id)
        storage.add_to_list("mark_me_{}".format(event_id), user.id)
        self.event = event
        self.accept()

    def add_user(self, event):
        pass

    def marked(self, params):
        user_id = params.get('user_id')
        if user_id is None or user_id != self.scope['user'].id:
            return
        self.send_json({"message": "marked", "params": {'user_id': 1234}})
        # TODO: check if responce is needed
        self.close()

    def disconnect(self, code):
        if self.event is not None:
            async_to_sync(self.channel_layer.group_discard)("event_{}".format(self.event.uuid), self.channel_name)
