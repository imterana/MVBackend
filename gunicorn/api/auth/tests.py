from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from ..misc.response import ResponseCode
from ..misc.test import APITestCase


class AuthTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user = User(username='test login')
        user.set_password('12345')
        user.save()
        cls.user = user

    def test_get_current_user_id(self):
        client = Client()
        client.force_login(self.user)

        response = client.get(reverse('get_current_user_id'))
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        user_id = parsed["response"]["user_id"]

        self.assertEqual(self.user.id, user_id)
