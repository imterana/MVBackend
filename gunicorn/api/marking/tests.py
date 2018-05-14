import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User

from .consumers import MarkingConsumer
from ..models import Event


@pytest.mark.django_db
@pytest.mark.asyncio
class TestMarking(object):
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        cls.user = user

    async def test_connection(self):
        user = self.user

        event = Event(creator=user)
        event.save()

        communicator = WebsocketCommunicator(MarkingConsumer, "ws/marking?event_id={eid}".format(eid=event.uuid))
        communicator.scope['user'] = user
        connected, subprotocol = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_connection_non_existing_event(self):
        user = self.user

        communicator = WebsocketCommunicator(MarkingConsumer, "ws/marking?event_id={eid}".format(eid='non-existing'))
        communicator.scope['user'] = user
        connected, subprotocol = await communicator.connect()
        assert connected

        response = await communicator.receive_output()
        assert response['type'] == 'websocket.close'
        await communicator.disconnect()

    async def test_connection_no_event(self):
        user = self.user

        communicator = WebsocketCommunicator(MarkingConsumer, "ws/marking")
        communicator.scope['user'] = user
        connected, subprotocol = await communicator.connect()
        assert connected

        response = await communicator.receive_output()
        assert response['type'] == 'websocket.close'
        await communicator.disconnect()
