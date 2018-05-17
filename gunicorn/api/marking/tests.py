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

    async def connect(self, user_type):
        if user_type == "mark_me":
            communicator = WebsocketCommunicator(MarkMeConsumer,
                                                 "ws/mark_me?event_id={eid}".format(eid=self.event.uuid))
            communicator.scope['user'] = self.mark_me_user
        elif user_type == "ready_to_mark":
            communicator = WebsocketCommunicator(MarkingConsumer,
                                                 "ws/marking?event_id={eid}".format(eid=self.event.uuid))
            communicator.scope['user'] = self.ready_to_mark_user
        else:
            raise NotImplementedError
        connected, _ = await communicator.connect()
        assert connected
        return communicator

    async def assert_successful_marking(self, mark_me_comm, ready_to_mark_comm):
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
        assert message == "marked"

        params = response.get('params')
        assert params == {'user_id': self.ready_to_mark_user.id}

    async def test_mark_me_first(self):
        mark_me_comm = await self.connect("mark_me")
        ready_to_mark_comm = await self.connect("ready_to_mark")

        response = await ready_to_mark_comm.receive_json_from()
        message = response.get('message')
        assert message == 'marking_list'
        params = response.get('params')
        marking_list = params.get('marking_list')
        assert marking_list == [self.mark_me_user.id]

        await self.assert_successful_marking(mark_me_comm=mark_me_comm, ready_to_mark_comm=ready_to_mark_comm)

        await mark_me_comm.disconnect()
        await ready_to_mark_comm.disconnect()

    async def test_ready_to_mark_first(self):
        ready_to_mark_comm = await self.connect("ready_to_mark")

        response = await ready_to_mark_comm.receive_json_from()
        message = response.get('message')
        assert message == 'marking_list'
        params = response.get('params')
        marking_list = params.get('marking_list')
        assert marking_list == []

        mark_me_comm = await self.connect("mark_me")

        response = await ready_to_mark_comm.receive_json_from()
        message = response.get('message')
        assert message == "user_joined"
        params = response.get('params')
        assert params == {'user_id': self.mark_me_user.id}

        await self.assert_successful_marking(mark_me_comm=mark_me_comm, ready_to_mark_comm=ready_to_mark_comm)

        await mark_me_comm.disconnect()
        await ready_to_mark_comm.disconnect()

    async def test_refuse_marking(self):
        mark_me_comm = await self.connect("mark_me")
        ready_to_mark_comm = await self.connect("ready_to_mark")

        response = await ready_to_mark_comm.receive_json_from()
        message = response.get('message')
        assert message == 'marking_list'
        params = response.get('params')
        marking_list = params.get('marking_list')
        assert marking_list == [self.mark_me_user.id]

        await ready_to_mark_comm.send_json_to(
            {"message": "prepare_to_mark", 'params': {'user_id': self.mark_me_user.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        await ready_to_mark_comm.send_json_to(
            {"message": "refuse_marking", 'params': {'user_id': self.mark_me_user.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        await self.assert_successful_marking(mark_me_comm=mark_me_comm, ready_to_mark_comm=ready_to_mark_comm)

        await mark_me_comm.disconnect()
        await ready_to_mark_comm.disconnect()

    async def test_several_mark_me(self):
        mark_me_user1 = create_user("mmu1")
        self.event.users.add(mark_me_user1)
        mark_me_comm1 = WebsocketCommunicator(MarkMeConsumer,
                                              "ws/mark_me?event_id={eid}".format(eid=self.event.uuid))
        mark_me_comm1.scope['user'] = mark_me_user1
        connected, _ = await mark_me_comm1.connect()
        assert connected

        mark_me_user2 = create_user("mmu2")
        self.event.users.add(mark_me_user2)
        mark_me_comm2 = WebsocketCommunicator(MarkMeConsumer,
                                              "ws/mark_me?event_id={eid}".format(eid=self.event.uuid))
        mark_me_comm2.scope['user'] = mark_me_user2
        connected, _ = await mark_me_comm2.connect()
        assert connected

        self.event.save()

        ready_to_mark_comm = await self.connect("ready_to_mark")
        response = await ready_to_mark_comm.receive_json_from()
        print(response)
        message = response.get('message')
        assert message == 'marking_list'
        params = response.get('params')
        marking_list = params.get('marking_list')
        assert set(marking_list) == {mark_me_user1.id, mark_me_user2.id}

        # Refuse marking mark_me_user1

        await ready_to_mark_comm.send_json_to(
            {"message": "prepare_to_mark", 'params': {'user_id': mark_me_user1.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        await ready_to_mark_comm.send_json_to(
            {"message": "refuse_marking", 'params': {'user_id': mark_me_user1.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        # Mark mark_me_user2

        await ready_to_mark_comm.send_json_to(
            {"message": "prepare_to_mark", 'params': {'user_id': mark_me_user2.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        await ready_to_mark_comm.send_json_to(
            {"message": "confirm_marking", 'params': {'user_id': mark_me_user2.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        response = await mark_me_comm2.receive_json_from()
        message = response.get('message')
        assert message == "marked"
        params = response.get('params')
        assert params == {'user_id': self.ready_to_mark_user.id}

        # Mark mark_me_user1

        await ready_to_mark_comm.send_json_to(
            {"message": "prepare_to_mark", 'params': {'user_id': mark_me_user1.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        await ready_to_mark_comm.send_json_to(
            {"message": "confirm_marking", 'params': {'user_id': mark_me_user1.id}})
        response = await ready_to_mark_comm.receive_json_from()
        assert response == {'result': 'ok'}

        response = await mark_me_comm1.receive_json_from()
        message = response.get('message')
        assert message == "marked"
        params = response.get('params')
        assert params == {'user_id': self.ready_to_mark_user.id}

        await mark_me_comm1.disconnect()
        await mark_me_comm2.disconnect()
        await ready_to_mark_comm.disconnect()
