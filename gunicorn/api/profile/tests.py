from django.test import Client
from django.urls import reverse

from ..misc.response import ResponseCode
from ..misc.test import APITestCase

from ..models import UserProfile


class UserProfileTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        profile = UserProfile(username='test name ')
        profile.user.set_password('12345')
        profile.picture = '/some/test/url'
        profile.bio = 'test institute, test department, test group'
        profile.confirmed = True
        profile.karma = 100500
        profile.save()
        cls.user_profile = profile

    def test_get_profile(self):
        client = Client()
        client.force_login(self.user_profile.user)

        response = client.get(reverse('get_profile'), {'user_id': self.user_profile.user.uuid})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        profile = parsed["response"]

        self.assertEqual(self.user_profile.user.username, profile["display_name"])
        self.assertEqual(self.user_profile.picture, profile["pic"])
        self.assertEqual(self.user_profile.confirmed, profile["confirmed"])
        self.assertEqual(self.user_profile.bio, profile['bio'])
        self.assertEqual(self.user_profile.karma, profile['karma'])

    def test_get_nonexisting_profile(self):
        client = Client()
        client.force_login(self.user_profile.user)

        nonexisting_id = 'none'

        response = client.get(reverse('get_profile'), {'user_id': nonexisting_id})
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_update_profile_name(self):
        client = Client()
        client.force_login(self.user_profile.user)

        new_name = 'new display name'
        response = client.post(reverse('update_profile_info'), {'display_name': new_name})
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)

        response = client.get(reverse('get_profile'), {'user_id': self.user_profile.user.uuid})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        profile = parsed["response"]

        self.assertEqual(new_name, profile["display_name"])

    def test_update_profile_bio(self):
        client = Client()
        client.force_login(self.user_profile.user)

        new_bio = 'new bio is a very cool bio'
        response = client.post(reverse('update_profile_info'), {'display_name': new_bio})
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)

        response = client.get(reverse('get_profile'), {'user_id': self.user_profile.user.uuid})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        profile = parsed["response"]

        self.assertEqual(new_bio, profile["bio"])

    def test_find_profile_by_name(self):
        client = Client()
        client.force_login(self.user_profile.user)

        name_part = 'test n'

        response = client.post(reverse('find_profile_by_name'), {'display_name_pert': name_part})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        self.assertEqual(1, parsed["response"].len)
        profile = parsed["response"][0]

        self.assertEqual(self.user_profile.user.uuid, profile["user_id"])
        self.assertEqual(self.user_profile.user.username, profile["display_name"])

    def test_find_nonexisting_profile_by_name(self):
        client = Client()
        client.force_login(self.user_profile.user)

        name_part = 'noexisting'

        response = client.post(reverse('find_profile_by_name'), {'display_name_pert': name_part})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        self.assertEqual(0, parsed["response"].len)

    def test_find_profile_by_short_name(self):
        client = Client()
        client.force_login(self.user_profile.user)

        name_part = 'tes'

        response = client.post(reverse('find_profile_by_name'), {'display_name_pert': name_part})
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_find_all_profiles(self):
        client = Client()
        client.force_login(self.user_profile.user)

        response = client.post(reverse('find_profile_by_name'))
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        self.assertEqual(1, parsed["response"].len)
        profile = parsed["response"][0]

        self.assertEqual(self.user_profile.user.uuid, profile["user_id"])
        self.assertEqual(self.user_profile.user.username, profile["display_name"])
