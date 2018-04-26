from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

import json

from ..misc.response import ResponseCode
from ..misc.test import APITestCase


class EventTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user = User(username='testuser')
        user.set_password('12345')
        user.save()
        cls.user = user

    def test_create_delete_event(self):
        client = Client()
        client.force_login(self.user)

        event_name = 'testevent'
        response = client.post(reverse('create_event'), {'name': event_name})
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

        response = client.post(reverse('delete_event'), {'event_id': event_id})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_OK)

        response = client.get(reverse('get_events'))
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        self.assertEqual(0, len(parsed["response"]))

    def test_leave_event(self):
        client = Client()
        client.force_login(self.user)

        event_name = 'testevent'
        response = client.post(reverse('create_event'), {'name': event_name})
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

        response = client.post(reverse('leave_event'), {'event_id': event_id})
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
        client = Client()
        client.force_login(self.user)
        event_name = 'testevent'

        response = client.post(reverse('create_event'), {'name': event_name})
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        client.post(reverse('leave_event'), {'event_id': event_id})

        response = client.post(reverse('join_event'), {'event_id': event_id})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_OK)

    def test_double_join_event(self):
        client = Client()
        client.force_login(self.user)
        event_name = 'testevent'

        response = client.post(reverse('create_event'), {'name': event_name})
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        response = client.post(reverse('join_event'), {'event_id': event_id})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_NOT_PERMITTED)

    def test_delete_nonexisting_event(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('delete_event'), {'event_id': 'none'})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_leave_nonexisting_event(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('leave_event'), {'event_id': 'none'})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_leave_nonexisting_event(self):
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('join_event'), {'event_id': 'none'})
        self.parseAndCheckResponseCode(response,
                                       ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_delete_not_own_event(self):
        user_2 = User(username='testuser_2')
        user_2.set_password('12345')
        user_2.save()
        client_2 = Client()
        client_2.force_login(user_2)
        response = client_2.post(reverse('create_event'), {'name': 'testevent'})
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        client = Client()
        client.force_login(self.user)
        response = client.post(reverse('delete_event'), {'event_id': event_id})
        parsed = self.parseAndCheckResponseCode(
                response,
                ResponseCode.RESPONSE_NOT_PERMITTED
        )

    def test_leave_not_joined_event(self):
        user_2 = User(username='testuser_2')
        user_2.set_password('12345')
        user_2.save()
        client_2 = Client()
        client_2.force_login(user_2)
        response = client_2.post(reverse('create_event'), {'name': 'testevent'})
        parsed = self.parseAndCheckResponseCode(response,
                                                ResponseCode.RESPONSE_OK)
        event_id = parsed["response"]["event_id"]

        client = Client()
        client.force_login(self.user)

        response = client.post(reverse('leave_event'), {'event_id': event_id})
        parsed = self.parseAndCheckResponseCode(
                response,
                ResponseCode.RESPONSE_NOT_PERMITTED
        )

    def test_create_duplicate_event(self):
        client = Client()
        client.force_login(self.user)

        event_name = 'testevent'
        client.post(reverse('create_event'), {'name': event_name})
        response = client.post(reverse('create_event'), {'name': event_name})
        self.parseAndCheckResponseCode(
                response,
                ResponseCode.RESPONSE_UNKNOWN_ERROR,
        )
