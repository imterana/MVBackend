from urllib.parse import parse_qs

from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ValidationError

from ..models import Event


def get_event_by_uuid(uuid):
    try:
        event = Event.objects.filter(uuid=uuid).first()
    except ValidationError:
        event = None
    return event


class MarkingConsumer(JsonWebsocketConsumer):
    messages = ['prepare_to_mark', 'confirm_marking', 'refuse_marking']

    def connect(self):
        params = parse_qs(self.scope['query_string'])
        event_id = params.get(b'event_id')
        if event_id is None:
            self.send_json({"error": "No event id"}, close=True)
            return

        event_id = event_id[0].decode('utf-8')

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
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive_json(self, content, **kwargs):
        pass
