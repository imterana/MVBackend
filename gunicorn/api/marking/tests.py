import datetime

import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User

from .consumers import MarkingConsumer, MarkMeConsumer
from ..models import Event


@pytest.mark.django_db(transaction=True)
def create_user(username):
    user = User(username=username)
    user.set_password('12345')
    user.save()
    return user


@pytest.mark.django_db(transaction=True)
def create_event(creator, time_from=None, time_to=None, name="test evemt"):
    event = Event(creator=creator)
    if time_to is not None:
        event.time_to = time_to
    if time_from is not None:
        event.time_from = time_from
    event.name = name
    event.save()
    event.users.set([creator])
    event.save()
    return event


def create_running_event(creator, name='running_event'):
    time_from = datetime.datetime.utcnow() - datetime.timedelta(seconds=12)
    time_to = time_from + datetime.timedelta(hours=12)
    return create_event(creator=creator, name=name, time_from=time_from, time_to=time_to)


class SharedEvent(object):
    __event = None

    @classmethod
    def __new__(cls, creator):
        if SharedEvent.__event is None:
            SharedEvent.__event = create_event(creator)
        return SharedEvent.__event


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestConsumer(object):
    route = ""
    user = None
    event = None

    async def assert_connection_fails(self, event_id=None, user=None):
        if event_id is None:
            event_id = self.event.uuid
        if user is None:
            user = self.user

        communicator = WebsocketCommunicator(MarkingConsumer, self.route + "?event_id={eid}".format(eid=event_id))
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        assert connected

        response = await communicator.receive_output()
        assert response['type'] == 'websocket.close'
        await communicator.disconnect()

    async def connection_non_existing_event(self):
        await self.assert_connection_fails(event_id='not exist')

    async def connection_no_event(self):
        communicator = WebsocketCommunicator(MarkingConsumer, "ws/marking")
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        assert connected

        response = await communicator.receive_output()
        assert response['type'] == 'websocket.close'
        await communicator.disconnect()

    async def connection_past_event(self):
        time_to = datetime.datetime.utcnow()
        time_from = time_to - datetime.timedelta(hours=12)
        event = create_event(creator=self.user,
                             time_from=time_from,
                             time_to=time_to,
                             name='past')

        await self.assert_connection_fails(event_id=event.uuid)

    async def connection_future_event(self):
        time_from = datetime.datetime.utcnow() + datetime.timedelta(seconds=12)
        time_to = time_from + datetime.timedelta(hours=12)
        event = create_event(creator=self.user,
                             time_from=time_from,
                             time_to=time_to,
                             name='future')

        await self.assert_connection_fails(event_id=event.uuid)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMarking(TestConsumer):
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls):
        cls.user = create_user("marking_test_user")
        cls.event = create_event(cls.user)
        cls.route = "ws/marking"

    async def test_connection_non_existing_event(self):
        await self.connection_non_existing_event()

    async def test_connection_no_event(self):
        await self.connection_no_event()

    async def test_connection_past_event(self):
        await self.connection_past_event()

    async def test_connection_future_event(self):
        await self.connection_past_event()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMarkMe(TestConsumer):
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls):
        cls.user = create_user("mark_me_test_user")
        cls.event = create_event(cls.user)
        cls.route = "ws/mark_me"

    async def test_connection(self):
        communicator = WebsocketCommunicator(MarkMeConsumer, self.route + "?event_id={eid}".format(eid=self.event.uuid))
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_connection_non_existing_event(self):
        await self.connection_non_existing_event()

    async def test_connection_no_event(self):
        await self.connection_no_event()

    async def test_connection_past_event(self):
        await self.connection_past_event()

    async def test_connection_future_event(self):
        await self.connection_past_event()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestInteraction(object):
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls):
        cls.mark_me_user = create_user("mark_me_test_user")
        cls.ready_to_mark_user = create_user("ready_to_mark_test_user")
        cls.event = create_running_event(cls.ready_to_mark_user)
        cls.event.users.add(cls.mark_me_user)
        cls.event.save()

    async def test_mark_me_first(self):
        mark_me_comm = WebsocketCommunicator(MarkMeConsumer,
                                             "ws/mark_me?event_id={eid}".format(eid=self.event.uuid))
        mark_me_comm.scope['user'] = self.mark_me_user
        connected, _ = await mark_me_comm.connect()
        assert connected

        ready_to_mark_comm = WebsocketCommunicator(MarkingConsumer,
                                                   "ws/marking?event_id={eid}".format(eid=self.event.uuid))
        ready_to_mark_comm.scope['user'] = self.ready_to_mark_user
        connected, _ = await ready_to_mark_comm.connect()
        assert connected

        response = await ready_to_mark_comm.receive_json_from()
        marking_list = response.get('marking_list')
        assert marking_list is not None
        assert len(marking_list) == 1
        assert marking_list[0] == self.mark_me_user.id

        await ready_to_mark_comm.send_json_to(
            {"message": "prepare_to_mark", 'params': {'user_id': self.mark_me_user.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        await ready_to_mark_comm.send_json_to(
            {"message": "confirm_marking", 'params': {'user_id': self.mark_me_user.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        response = await mark_me_comm.receive_json_from()
        message = response.get('message')
        assert message is not None
        params = response.get('params')
        assert params is not None
        marked_user_id = params.get('user_id')
        assert marked_user_id is not None

        assert marked_user_id == self.ready_to_mark_user.id

        await mark_me_comm.disconnect()
        await ready_to_mark_comm.disconnect()
