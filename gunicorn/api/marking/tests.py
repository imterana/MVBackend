import asyncio
import datetime

import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User

from .consumers import MarkingConsumer, MarkMeConsumer, ErrorMessages, EncouragingMessages
from .websocket_api import ClientResponse, ClientMessages
from ..models import Event, UserProfile


# TODO test what if we don't receive any answer when it is expected

@pytest.mark.django_db(transaction=True)
def create_user(username):
    user = User(username=username)
    user.set_password('12345')
    user.save()
    return user


@pytest.mark.django_db(transaction=True)
def create_event(creator, time_from=None, time_to=None, name="test event"):
    event = Event(creator=creator)
    if time_from is not None:
        event.time_from = time_from
    else:
        event.time_from = datetime.datetime.utcnow() - datetime.timedelta(seconds=12)

    if time_to is not None:
        event.time_to = time_to
    else:
        event.time_to = event.time_from + datetime.timedelta(hours=12)

    event.name = name
    event.save()
    event.users.set([creator])
    event.save()
    return event


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestConsumer(object):
    route = ""
    consumer = None
    user = None
    event = None

    async def assert_connection_fails(self, event_id=None, user=None, error_msg=None):
        if event_id is None:
            event_id = self.event.uuid
        if user is None:
            user = self.user

        communicator = WebsocketCommunicator(self.consumer, self.route + "?event_id={eid}".format(eid=event_id))
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        assert connected

        if error_msg is not None:
            response = await communicator.receive_json_from()
            assert response == ClientResponse.response_error(error_msg)

        response = await communicator.receive_output()
        assert response['type'] == 'websocket.close'
        await communicator.disconnect()

    async def connection_non_existing_event(self):
        await self.assert_connection_fails(event_id='not exist', error_msg=ErrorMessages.INVALID_EVENT)

    async def connection_no_event(self):
        communicator = WebsocketCommunicator(self.consumer, self.route)
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        assert connected

        response = await communicator.receive_json_from()
        assert response == ClientResponse.response_error(ErrorMessages.NO_EVENT)

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

        await self.assert_connection_fails(event_id=event.uuid, error_msg=ErrorMessages.PAST_EVENT)

    async def connection_future_event(self):
        time_from = datetime.datetime.utcnow() + datetime.timedelta(minutes=12)
        time_to = time_from + datetime.timedelta(hours=12)
        event = create_event(creator=self.user,
                             time_from=time_from,
                             time_to=time_to,
                             name='future')

        await self.assert_connection_fails(event_id=event.uuid, error_msg=ErrorMessages.NOT_RUNNING_EVENT)

    async def connection_after_asking_to_mark(self):
        communicator = WebsocketCommunicator(MarkMeConsumer, "ws/mark_me?event_id={eid}".format(eid=self.event.uuid))
        communicator.scope['user'] = self.user
        connected, _ = await communicator.connect()
        assert connected

        # Allows the event loop to give the flow to the websocket consumer
        await asyncio.sleep(1)

        await self.assert_connection_fails(error_msg=ErrorMessages.NOT_PERMITTED)

        await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMarking(TestConsumer):
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls):
        cls.user = create_user("marking_test_user")
        cls.event = create_event(cls.user)
        cls.route = "ws/marking"
        cls.consumer = MarkingConsumer

    async def test_connection_non_existing_event(self):
        await self.connection_non_existing_event()

    async def test_connection_no_event(self):
        await self.connection_no_event()

    async def test_connection_past_event(self):
        await self.connection_past_event()

    async def test_connection_future_event(self):
        await self.connection_future_event()

    async def test_connection_after_asking_to_mark(self):
        await self.connection_after_asking_to_mark()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestMarkMe(TestConsumer):
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls):
        cls.user = create_user("mark_me_test_user")
        cls.event = create_event(cls.user)
        cls.route = "ws/mark_me"
        cls.consumer = MarkMeConsumer

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

    async def test_connection_after_asking_to_mark(self):
        await self.connection_after_asking_to_mark()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestInteraction(object):
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls):
        cls.mark_me_user = create_user("mark_me_test_user")
        cls.ready_to_mark_user = create_user("ready_to_mark_test_user")
        cls.event = create_event(cls.ready_to_mark_user)
        cls.event.users.add(cls.mark_me_user)
        cls.event.save()

    async def connect(self, user_type, user=None):
        if user_type == "mark_me":
            communicator = WebsocketCommunicator(MarkMeConsumer,
                                                 "ws/mark_me?event_id={eid}".format(eid=self.event.uuid))
            if user is None:
                communicator.scope['user'] = self.mark_me_user

        elif user_type == "ready_to_mark":
            communicator = WebsocketCommunicator(MarkingConsumer,
                                                 "ws/marking?event_id={eid}".format(eid=self.event.uuid))
            if user is None:
                communicator.scope['user'] = self.ready_to_mark_user
        else:
            raise NotImplementedError

        if user:
            communicator.scope['user'] = user

        print(communicator.scope['user'])

        connected, _ = await communicator.connect()
        assert connected
        return communicator

    async def assert_successful_marking(self, mark_me_comm, ready_to_mark_comm, ready_to_mark_user=None):
        await self.assert_successful_prepare_to_mark(ready_to_mark_comm, self.mark_me_user.id)

        profile = UserProfile.objects.filter(user=self.ready_to_mark_user).first()
        if profile is None:
            profile = UserProfile(user=self.ready_to_mark_user)
            profile.save()
        karma = profile.karma

        await self.assert_successful_confirm_marking(ready_to_mark_comm)

        await asyncio.sleep(1)

        profile = UserProfile.objects.filter(user=self.ready_to_mark_user).first()
        assert karma + EncouragingMessages.general_delta == profile.karma

        await self.assert_successful_was_marked(mark_me_comm, self.ready_to_mark_user.id)

    @staticmethod
    async def assert_successful_prepare_to_mark(ready_to_mark_comm, mark_me_user_id):
        await ready_to_mark_comm.send_json_to(
            {"message": "prepare_to_mark", 'params': {'user_id': mark_me_user_id}})

        response = await ready_to_mark_comm.receive_json_from()

        assert response == ClientResponse.response_ok(ClientMessages.PREPARED)

    @staticmethod
    async def assert_successful_confirm_marking(ready_to_mark_comm):
        await ready_to_mark_comm.send_json_to(
            {"message": "confirm_marking"})

        response = await ready_to_mark_comm.receive_json_from()

        assert response.get('result') == 'ok'
        assert response.get('message') == ClientMessages.MARKED
        display_msg = response.get("params", {}).get("display_msg")
        assert display_msg in EncouragingMessages.general

    @staticmethod
    async def assert_successful_refuse_to_mark(ready_to_mark_comm):
        await ready_to_mark_comm.send_json_to(
            {"message": "refuse_to_mark"})

        response = await ready_to_mark_comm.receive_json_from()

        assert response == ClientResponse.response_ok(message=ClientMessages.REFUSED)

    @staticmethod
    async def assert_successful_was_marked(mark_me_comm, ready_to_mark_user_id):
        response = await mark_me_comm.receive_json_from()
        assert response == ClientResponse.response_ok(ClientMessages.WAS_MARKED,
                                                      params={'user_id': ready_to_mark_user_id})

    @staticmethod
    async def assert_valid_marking_list(ready_to_mark_comm, marking_list):
        response = await ready_to_mark_comm.receive_json_from()
        assert response.get('result') == 'ok'
        assert response.get('message') == 'marking_list'
        assert set(response.get('params').get('marking_list')) == set(marking_list)

    async def test_mark_me_first(self):
        mark_me_comm = await self.connect("mark_me")

        # Allows the event loop to give the flow to the websocket consumer
        await asyncio.sleep(1)

        ready_to_mark_comm = await self.connect("ready_to_mark")

        response = await ready_to_mark_comm.receive_json_from()
        assert response == ClientResponse.response_ok(message=ClientMessages.MARKING_LIST,
                                                      params={'marking_list': [self.mark_me_user.id]})

        await self.assert_successful_marking(mark_me_comm=mark_me_comm, ready_to_mark_comm=ready_to_mark_comm)

        await mark_me_comm.disconnect()
        await ready_to_mark_comm.disconnect()

    async def test_ready_to_mark_first(self):
        ready_to_mark_comm = await self.connect("ready_to_mark")

        response = await ready_to_mark_comm.receive_json_from()
        assert response == ClientResponse.response_ok(message=ClientMessages.MARKING_LIST,
                                                      params={'marking_list': []})

        mark_me_comm = await self.connect("mark_me")

        response = await ready_to_mark_comm.receive_json_from()
        assert response == ClientResponse.response_ok(message=ClientMessages.USER_JOINED,
                                                      params={'user_id': self.mark_me_user.id})

        await self.assert_successful_marking(mark_me_comm=mark_me_comm, ready_to_mark_comm=ready_to_mark_comm)

        await mark_me_comm.disconnect()
        await ready_to_mark_comm.disconnect()

    async def test_refuse_to_mark(self):
        mark_me_comm = await self.connect("mark_me")

        # Allows the event loop to give the flow to the websocket consumer
        await asyncio.sleep(1)

        ready_to_mark_comm = await self.connect("ready_to_mark")

        response = await ready_to_mark_comm.receive_json_from()
        assert response == ClientResponse.response_ok(message=ClientMessages.MARKING_LIST,
                                                      params={'marking_list': [self.mark_me_user.id]})

        await self.assert_successful_prepare_to_mark(ready_to_mark_comm, self.mark_me_user.id)

        await self.assert_successful_refuse_to_mark(ready_to_mark_comm)

        await self.assert_successful_marking(mark_me_comm=mark_me_comm, ready_to_mark_comm=ready_to_mark_comm)

        await mark_me_comm.disconnect()
        await ready_to_mark_comm.disconnect()

    async def test_several_mark_me(self):
        mark_me_user1 = create_user("mmu1")
        self.event.users.add(mark_me_user1)
        mark_me_comm1 = await self.connect("mark_me", user=mark_me_user1)

        mark_me_user2 = create_user("mmu2")
        self.event.users.add(mark_me_user2)
        mark_me_comm2 = await self.connect("mark_me", user=mark_me_user2)

        self.event.save()

        # Allows the event loop to give the flow to the websocket consumer
        await asyncio.sleep(1)

        ready_to_mark_comm = await self.connect("ready_to_mark")
        await self.assert_valid_marking_list(ready_to_mark_comm, {mark_me_user1.id, mark_me_user2.id})

        # Refuse to mark mark_me_user1

        await self.assert_successful_prepare_to_mark(ready_to_mark_comm, mark_me_user1.id)
        await self.assert_successful_refuse_to_mark(ready_to_mark_comm)

        # Mark mark_me_user2

        await self.assert_successful_marking(ready_to_mark_comm=ready_to_mark_comm,
                                             mark_me_comm=mark_me_comm2)

        # Mark mark_me_user1

        await self.assert_successful_marking(ready_to_mark_comm=ready_to_mark_comm,
                                             mark_me_comm=mark_me_comm1)

        await mark_me_comm1.disconnect()
        await mark_me_comm2.disconnect()
        await ready_to_mark_comm.disconnect()
