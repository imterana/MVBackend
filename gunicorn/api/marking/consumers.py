import random
from datetime import datetime
from urllib.parse import parse_qs

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from .misc.client_communication import ClientResponse, ClientMessages, ErrorMessages, EncouragingMessages
from .misc.websocket_decorators import require_group_message_param, require_client_message_param, ignore_own_messages
from .storage import storage
from ..events.views import get_event_by_uuid
from ..models import UserProfile


def retrieve_event_id(query_string):
    params = parse_qs(query_string)
    event_id = params.get(b'event_id')
    if event_id is None or len(event_id) != 1:
        return None

    return event_id[0].decode('utf-8')


def event_is_running(event):
    time_from = datetime.utcfromtimestamp(event.time_from.timestamp())
    time_to = datetime.utcfromtimestamp(event.time_to.timestamp())
    now = datetime.utcnow()
    return not (time_from > now or time_to < now)


def event_is_over(event):
    time_to = datetime.utcfromtimestamp(event.time_to.timestamp())
    now = datetime.utcnow()
    return time_to < now


def increase_karma(user, delta: int):
    profile = UserProfile.objects.filter(user=user).first()
    profile.karma += delta
    profile.save()


class EventConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = None
        self.user = None

    def connect(self):
        self.accept()

        self.user = self.scope['user']

        event_id = retrieve_event_id(self.scope['query_string'])
        if event_id is None:
            self.send_json(ClientResponse.response_error(ErrorMessages.NO_EVENT), close=True)
            return False

        event = get_event_by_uuid(event_id)
        if event is None:
            self.send_json(ClientResponse.response_error(ErrorMessages.INVALID_EVENT), close=True)
            return False

        asked_to_mark_list = [int(o.decode('utf-8')) for o in storage.get_list("asked_to_mark_{}".format(event_id))]
        if self.user.id in asked_to_mark_list:
            self.send_json(ClientResponse.response_error(ErrorMessages.NOT_PERMITTED), close=True)
            return False

        if event_is_over(event):
            self.send_json(ClientResponse.response_error(ErrorMessages.PAST_EVENT), close=True)
            return False

        self.event = event

        return True


class MarkingConsumer(EventConsumer):
    messages = ['prepare_to_mark', 'confirm_marking', 'refuse_to_mark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marking_list = set()
        self.prepared_user_id = None

    def connect(self):
        if not super().connect():
            return

        if not event_is_running(self.event):
            self.send_json(ClientResponse.response_error(ErrorMessages.NOT_RUNNING_EVENT), close=True)
            return False

        marking_list = [int(o.decode('utf-8')) for o in storage.get_list("mark_me_{}".format(self.event.uuid))]
        self.marking_list = set(marking_list)

        async_to_sync(self.channel_layer.group_add)("event_{}".format(self.event.uuid), self.channel_name)
        storage.add_to_list("ready_to_mark_{}".format(self.event.uuid), self.user.id)

        self.send_json(ClientResponse.response_ok(message=ClientMessages.MARKING_LIST,
                                                  params={"marking_list": marking_list}))

    def disconnect(self, close_code):
        if self.event is not None:
            storage.remove_from_list("ready_to_mark_{}".format(self.event.uuid), self.user.id)
            async_to_sync(self.channel_layer.group_discard)("event_{}".format(self.event.uuid), self.channel_name)

    def receive_json(self, content, **kwargs):
        print("Message from client", content)
        if content["message"] in self.messages:
            getattr(self, content["message"])(content.get("params"))
        else:
            self.send_json(ClientResponse.response_error(ErrorMessages.NO_MESSAGE))

    @require_client_message_param(['user_id'])
    def prepare_to_mark(self, params):
        global_list = storage.get_list("mark_me_{}".format(self.event.uuid))
        print("prepare to mark {}  user id {} ### my marking list: {} ### global: {} ### prepared user id: {}"
              .format(self.user.id, params['user_id'], self.marking_list, global_list, self.prepared_user_id))

        user_id = params['user_id']
        if self.prepared_user_id is not None:
            self.send_json(ClientResponse.response_error(ErrorMessages.ALREADY_HAVE_USER))
            return

        if not storage.remove_from_list("mark_me_{}".format(self.event.uuid), user_id):
            self.send_json(ClientResponse.response_error(ErrorMessages.USER_ALREADY_CHOSEN))
            return

        self.marking_list.remove(user_id)
        self.prepared_user_id = user_id

        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'group.do.not.mark',
                "params": {"user_id": user_id},
                "sender": self.channel_name
            }
        )

        self.send_json(ClientResponse.response_ok(message=ClientMessages.PREPARED))

    def confirm_marking(self, params):
        global_list = storage.get_list("mark_me_{}".format(self.event.uuid))
        print("confirm marking {} ### my marking list: {} ### global: {} ### prepared user id: {}"
              .format(self.user.id, self.marking_list, global_list, self.prepared_user_id))

        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'group.marked',
                "params": {"mark_me_user_id": self.prepared_user_id,
                           "ready_to_mark_user_id": self.scope['user'].id},
                "sender": self.channel_name
            }
        )

        self.prepared_user_id = None
        self.send_json(ClientResponse.response_ok(message=ClientMessages.MARKED,
                                                  params={"display_msg": random.choice(EncouragingMessages.general)}))

        increase_karma(self.user, EncouragingMessages.general_delta)

    def refuse_to_mark(self, params):
        if self.prepared_user_id is None:
            self.send_json(ClientResponse.response_error(ErrorMessages.NOT_PERMITTED))
            return

        global_list = storage.get_list("mark_me_{}".format(self.event.uuid))
        print(
            "refuse to mark {} ### my marking list: {} ### global: {} ### prepared user id: {}"
                .format(self.user.id, self.marking_list, global_list, self.prepared_user_id))

        storage.add_to_list("mark_me_{}".format(self.event.uuid), self.prepared_user_id)
        self.marking_list.add(self.prepared_user_id)

        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'group.mark.me',
                "params": {"user_id": self.prepared_user_id},
                "sender": self.channel_name
            }
        )
        self.prepared_user_id = None
        self.send_json(ClientResponse.response_ok(message=ClientMessages.REFUSED))

    def group_marked(self, params):
        pass

    @ignore_own_messages
    @require_group_message_param(["user_id"])
    def group_mark_me(self, params):
        self.marking_list.add(params['user_id'])
        self.send_json(ClientResponse.response_ok(message=ClientMessages.USER_JOINED,
                                                  params={'user_id': params['user_id']}))

    @ignore_own_messages
    @require_group_message_param(["user_id"])
    def group_do_not_mark(self, params):
        try:
            self.marking_list.remove(params['user_id'])
        except KeyError:
            print("Ready to mark user id {rtmuid}, user id to remove {uid}, marking list {ml}"
                  .format(rtmuid=self.user.id, uid=params['user_id'], ml=self.marking_list))
            return
        self.send_json(ClientResponse.response_ok(message=ClientMessages.USER_LEFT,
                                                  params={'user_id': params['user_id']}))


class MarkMeConsumer(EventConsumer):
    def connect(self):
        if not super().connect():
            return

        async_to_sync(self.channel_layer.group_add)("event_{}".format(self.event.uuid), self.channel_name)
        async_to_sync(self.channel_layer.group_send)(
            "event_{}".format(self.event.uuid),
            {
                'type': 'group.mark.me',
                "params": {"user_id": self.user.id},
                "sender": self.channel_name
            }
        )

        storage.add_to_list("mark_me_{}".format(self.event.uuid), self.user.id)
        storage.add_to_list("asked_to_mark_{}".format(self.event.uuid), self.user.id)

    def group_mark_me(self, params):
        pass

    def group_do_not_mark(self, params):
        pass

    @ignore_own_messages
    @require_group_message_param(["ready_to_mark_user_id", "mark_me_user_id"])
    def group_marked(self, params):
        self.send_json(ClientResponse.response_ok(message=ClientMessages.WAS_MARKED,
                                                  params={'user_id': params['ready_to_mark_user_id']}),
                       close=True)

    def disconnect(self, code):
        if self.event is not None:
            async_to_sync(self.channel_layer.group_discard)("event_{}".format(self.event.uuid), self.channel_name)
