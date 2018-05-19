from datetime import datetime
from urllib.parse import parse_qs

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ValidationError

from .misc.websocket_decorators import require_group_message_param, require_client_message_param, ignore_myself
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
    messages = ['prepare_to_mark', 'confirm_marking', 'refuse_to_mark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marking_list = set()
        self.event = None
        self.prepared_user_id = None

    def connect(self):
        event_id = retrieve_event_id(self.scope['query_string'])
        if event_id is None:
            self.send_json({"result": "error", "error_msg": "No event id"}, close=True)
            return

        event = get_event_by_uuid(event_id)
        if event is None:
            self.send_json({"result": "error", "error_msg": "Invalid event"})
            self.close()
            return

        time_from = datetime.utcfromtimestamp(event.time_from.timestamp())
        time_to = datetime.utcfromtimestamp(event.time_to.timestamp())
        now = datetime.utcnow()
        if time_from > now or time_to < now:
            self.send_json({"result": "error", "error_msg": "Event is not running now"})
            self.close()
            return

        user = self.scope['user']

        self.accept()

        print(storage.get_list("mark_me_{}".format(event_id)), event_id)
        marking_list = [int(o.decode('utf-8')) for o in storage.get_list("mark_me_{}".format(event_id))]
        self.marking_list = set(marking_list)
        self.event = event

        async_to_sync(self.channel_layer.group_add)("event_{}".format(event_id), self.channel_name)
        storage.add_to_list("ready_to_mark_{}".format(event_id), user.id)
        self.send_json({"message": 'marking_list', "params": {"marking_list": marking_list}})

    def disconnect(self, close_code):
        if self.event is not None:
            async_to_sync(self.channel_layer.group_discard)("event_{}".format(self.event.uuid), self.channel_name)
            storage.remove_from_list("ready_to_mark_{}".format(self.event.uuid), self.scope['user'].id)

    def receive_json(self, content, **kwargs):
        if content["message"] in self.messages:
            getattr(self, content["message"])(content.get("params"))
        else:
            self.send_json({"error": "No message"})

    @require_client_message_param(['user_id'])
    def prepare_to_mark(self, params):
        user_id = params['user_id']
        if self.prepared_user_id is not None:
            self.send_json({"result": "denial"})
            return
        self.prepared_user_id = user_id

        storage.remove_from_list("mark_me_{}".format(self.event.uuid), user_id)
        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'group.do.not.mark',
                "params": {"user_id": user_id},
                "sender": self.channel_name
            }
        )

        self.send_json({"result": "ok"})

    @require_client_message_param(['user_id'])
    def confirm_marking(self, params):
        user_id = params['user_id']
        if self.prepared_user_id != user_id:
            self.send_json({"result": "denial"})
            return
        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'group.marked',
                "params": {"mark_me_user_id": user_id,
                           "ready_to_mark_user_id": self.scope['user'].id},
                "sender": self.channel_name
            }
        )

        self.prepared_user_id = None
        self.send_json({"result": "ok"})

    @require_client_message_param(['user_id'])
    def refuse_to_mark(self, params):
        user_id = params.get('user_id')
        if self.prepared_user_id != user_id:
            return

        storage.add_to_list("mark_me_{}".format(self.event.uuid), user_id)
        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'group.mark.me',
                "params": {"user_id": self.prepared_user_id},
                "sender": self.channel_name
            }
        )
        self.prepared_user_id = None
        self.send_json({"result": "ok"})

    def group_marked(self, params):
        pass

    @ignore_myself
    @require_group_message_param(["user_id"])
    def group_mark_me(self, params):
        self.marking_list.add(params['user_id'])
        self.send_json({'message': 'user_joined', "params": {'user_id': params['user_id']}})

    @ignore_myself
    @require_group_message_param(["user_id"])
    def group_do_not_mark(self, params):
        print(params['user_id'], self.prepared_user_id)
        if params['user_id'] == self.prepared_user_id:
            return
        try:
            self.marking_list.remove(params['user_id'])
        except KeyError:
            return
        self.send_json({'message': 'user_left', "params": {'user_id': params['user_id']}})


class MarkMeConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = None

    def connect(self):
        event_id = retrieve_event_id(self.scope['query_string'])
        if event_id is None:
            self.close()
            return
        event = get_event_by_uuid(event_id)
        if event is None:
            self.close()
            return
        self.event = event

        user = self.scope['user']
        async_to_sync(self.channel_layer.group_add)("event_{}".format(event_id), self.channel_name)
        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(event_id),
            {
                'type': 'group.mark.me',
                "params": {"user_id": user.id},
                "sender": self.channel_name
            }
        )

        storage.add_to_list("mark_me_{}".format(event_id), user.id)
        self.accept()

    def group_mark_me(self, params):
        pass

    def group_do_not_mark(self, params):
        pass

    @ignore_myself
    @require_group_message_param(["ready_to_mark_user_id", "mark_me_user_id"])
    def group_marked(self, params):
        if params['mark_me_user_id'] != self.scope['user'].id:
            return
        self.send_json({"message": "marked", "params": {'user_id': params['ready_to_mark_user_id']}})
        self.close()

    def disconnect(self, code):
        if self.event is not None:
            async_to_sync(self.channel_layer.group_discard)("event_{}".format(self.event.uuid), self.channel_name)
