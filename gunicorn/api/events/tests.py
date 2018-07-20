import datetime
import json

from django.contrib.auth.models import User
from django.urls import reverse

from ..misc.response import ResponseCode
from ..misc.test import APITestCase, JSONClient
from ..misc.time import datetime_to_string
from ..models import Event


class EventTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        cls.user = user

    @staticmethod
    def create_event(client: JSONClient, name):
        time_from = datetime.datetime.utcnow() + datetime.timedelta(hours=12)
        time_to = time_from + datetime.timedelta(hours=1)
        time_from = datetime_to_string(time_from)
        time_to = datetime_to_string(time_to)
        return client.post_json(reverse('create_event'), {'name': name,
                                                          'time_from': time_from,
                                                          'time_to': time_to})

    def test_get_event_by_id(self):
        client = JSONClient()
        client.force_login(self.user)

        event_name = 'testevent'
        response = self.create_event(client, event_name)
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)

        event_id = parsed["response"]["event_id"]

        response = client.get(reverse('get_event_by_id'), {'event_id': event_id})
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event = parsed['response']
        self.assertEqual(event_name, event['name'])

    def test_create_delete_event(self):
        client = JSONClient()
        client.force_login(self.user)

        event_name = 'testevent'
        response = self.create_event(client, event_name)
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        response = client.get(reverse('get_events'))
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        self.assertEqual(1, len(parsed["response"]))
        event = parsed["response"][0]
        self.assertEqual(event_id, event["event_id"])
        self.assertEqual(event_name, event["name"])

        response = client.post_json(path=reverse('delete_event'), message={'event_id': str(event_id)})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_OK)

        response = client.get(reverse('get_events'))
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        self.assertEqual(0, len(parsed["response"]))

    def test_leave_event(self):
        client = JSONClient()
        client.force_login(self.user)

        event_name = 'testevent'
        response = self.create_event(client, event_name)
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        response = client.get(reverse('get_joined_events'))
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        self.assertEqual(1, len(parsed["response"]))
        event = parsed["response"][0]
        self.assertEqual(event_name, event["name"])
        self.assertEqual(event_id, event["event_id"])
        self.assertTrue(event["creator"])

        response = client.get(reverse('get_created_events'))
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        self.assertEqual(1, len(parsed["response"]))
        event = parsed["response"][0]
        self.assertEqual(event_name, event["name"])
        self.assertEqual(event_id, event["event_id"])

        response = client.post_json(path=reverse('leave_event'), message={'event_id': event_id})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_OK)

        response = client.get(reverse('get_joined_events'))
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        self.assertEqual(0, len(parsed["response"]))

        response = client.get(reverse('get_created_events'))
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        self.assertEqual(1, len(parsed["response"]))
        event = parsed["response"][0]
        self.assertEqual(event_name, event["name"])
        self.assertEqual(event_id, event["event_id"])

    def test_join_event(self):
        client = JSONClient()
        client.force_login(self.user)
        event_name = 'testevent'

        response = self.create_event(client, event_name)
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        client.post_json(reverse('leave_event'), {'event_id': event_id})

        response = client.post_json(path=reverse('join_event'), message={'event_id': event_id})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_OK)

    def test_double_join_event(self):
        client = JSONClient()
        client.force_login(self.user)
        event_name = 'testevent'

        response = self.create_event(client, event_name)
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        response = client.post_json(reverse('join_event'), {'event_id': event_id})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_NOT_PERMITTED)

    def test_delete_nonexisting_event(self):
        client = JSONClient()
        client.force_login(self.user)
        response = client.post_json(path=reverse('delete_event'), message={'event_id': 'none'})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_leave_nonexisting_event(self):
        client = JSONClient()
        client.force_login(self.user)
        response = client.post_json(path=reverse('leave_event'), message={'event_id': 'none'})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_join_nonexisting_event(self):
        client = JSONClient()
        client.force_login(self.user)
        response = client.post_json(reverse('join_event'), {'event_id': 'none'})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_delete_not_own_event(self):
        user_2 = User(username='testuser_2')
        user_2.set_password('12345')
        user_2.save()
        client_2 = JSONClient()
        client_2.force_login(user_2)
        event_name = 'testevent'
        response = self.create_event(client_2, event_name)
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        client = JSONClient()
        client.force_login(self.user)
        response = client.post_json(reverse('delete_event'), {'event_id': event_id})
        parsed = self.parseAndCheckResponseCode(
            response,
            ResponseCode.RESPONSE_NOT_PERMITTED
        )

    def test_leave_not_joined_event(self):
        user_2 = User(username='testuser_2')
        user_2.set_password('12345')
        user_2.save()
        client_2 = JSONClient()
        client_2.force_login(user_2)
        event_name = 'testevent'
        response = self.create_event(client_2, event_name)
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        client = JSONClient()
        client.force_login(self.user)

        response = client.post_json(reverse('leave_event'), {'event_id': event_id})
        parsed = self.parseAndCheckResponseCode(
            response,
            ResponseCode.RESPONSE_NOT_PERMITTED
        )

    def test_create_duplicate_event(self):
        client = JSONClient()
        client.force_login(self.user)

        event_name = 'testevent'
        response = self.create_event(client, event_name)
        response = self.create_event(client, event_name)
        self.parseAndCheckResponseCode(
            response,
            ResponseCode.RESPONSE_UNKNOWN_ERROR,
        )

    def test_filter_by_name(self):
        client = JSONClient()
        client.force_login(self.user)

        event1_name = 'testevent'
        event2_name = 'tesevent'

        response = self.create_event(client, event1_name)
        response = self.create_event(client, event2_name)

        response = client.get(reverse('get_events'), {'name': event1_name})
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)

        self.assertEqual(1, len(parsed["response"]))
        self.assertEqual(event1_name, parsed["response"][0]["name"])

        response = client.get(reverse('get_events'), {'name': 'tes'})
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)

        self.assertEqual(2, len(parsed["response"]))
        names = set(map(lambda x: x["name"], parsed["response"]))
        self.assertSetEqual({event1_name, event2_name}, names)

    def test_create_event_incorrect_time(self):
        client = JSONClient()
        client.force_login(self.user)
        event_name = 'testevent'

        time_from = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
        time_to = time_from + datetime.timedelta(minutes=1)
        time_from = datetime_to_string(time_from)
        time_to = datetime_to_string(time_to)

        response = client.post_json(reverse('create_event'), {'name': event_name,
                                                              'time_from': time_from,
                                                              'time_to': time_to})

        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_INVALID_ARGUMENT)

        response = client.post_json(reverse('create_event'), {'name': event_name,
                                                              'time_from': time_to,
                                                              'time_to': time_from})

        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_join_event_incorrect_time(self):
        client = JSONClient()
        client.force_login(self.user)

        time_from = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
        time_to = time_from + datetime.timedelta(minutes=1)
        event = Event(creator=self.user,
                      time_from=time_from,
                      time_to=time_to,
                      name='testevent')
        event.save()
        event_id = event.uuid

        response = client.post_json(reverse('join_event'), {'event_id': str(event_id)})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_NOT_PERMITTED)

        event.time_to = datetime.datetime.utcnow() + \
                        datetime.timedelta(hours=12)
        event.save()

        response = client.post_json(reverse('join_event'), {'event_id': str(event_id)})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_NOT_PERMITTED)

    def test_leave_event_late(self):
        client = JSONClient()
        client.force_login(self.user)

        time_from = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
        time_to = time_from + datetime.timedelta(minutes=1)
        event = Event(creator=self.user,
                      time_from=time_from,
                      time_to=time_to,
                      name='testevent')
        event.users.set([self.user])
        event.save()
        event_id = event.uuid

        response = client.post_json(reverse('leave_event'), {'event_id': str(event_id)})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_NOT_PERMITTED)

    def test_delete_event_late(self):
        client = JSONClient()
        client.force_login(self.user)

        time_from = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
        time_to = time_from + datetime.timedelta(minutes=1)
        event = Event(creator=self.user,
                      time_from=time_from,
                      time_to=time_to,
                      name='testevent')
        event.users.set([self.user])
        event.save()
        event_id = event.uuid

        response = client.post_json(reverse('leave_event'), {'event_id': str(event_id)})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_NOT_PERMITTED)
