import base64
import json
import os

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from ..misc.response import ResponseCode
from ..misc.test import APITestCase
from ..models import UserProfile

TEST_FILES_DIR = "/usr/src/test_files/"


class UserProfileTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user = User(username='test login')
        user.set_password('12345')
        user.save()

        profile = UserProfile(user=user)
        profile.display_name = 'test display name'
        profile.picture = '/some/test/url'
        profile.bio = 'test institute, test department, test group'
        profile.confirmed = True
        profile.karma = 100500
        profile.save()
        cls.user_profile = profile

    def test_get_profile(self):
        client = Client()
        client.force_login(self.user_profile.user)

        response = client.get(reverse('get_profile'), {'user_id': self.user_profile.user.id},
                              content_type='application/json')
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        profile = parsed["response"]

        self.assertEqual(self.user_profile.display_name, profile["display_name"])
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
        response = client.post(reverse('update_profile_info'), json.dumps({'display_name': new_name}),
                               content_type='application/json')
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)

        response = client.get(reverse('get_profile'), {'user_id': self.user_profile.user.id})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        profile = parsed["response"]

        self.assertEqual(new_name, profile["display_name"])

    def test_update_profile_bio(self):
        client = Client()
        client.force_login(self.user_profile.user)

        new_bio = 'new bio is a very cool bio'
        response = client.post(reverse('update_profile_info'), json.dumps({'bio': new_bio}),
                               content_type='application/json')
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)

        response = client.get(reverse('get_profile'), {'user_id': self.user_profile.user.id})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        profile = parsed["response"]

        self.assertEqual(new_bio, profile["bio"])

    def test_update_profile_without_parameters(self):
        client = Client()
        client.force_login(self.user_profile.user)

        response = client.post(reverse('update_profile_info'), json.dumps({}),
                               content_type='application/json')
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_MISSING_ARGUMENT)

    def test_find_profile_by_name(self):
        client = Client()
        client.force_login(self.user_profile.user)

        name_part = self.user_profile.display_name[:5]

        response = client.get(reverse('find_profile_by_name'), {'display_name_part': name_part})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        self.assertEqual(1, len(parsed["response"]))
        profile = parsed["response"][0]

        self.assertEqual(self.user_profile.user.id, profile["user_id"])
        self.assertEqual(self.user_profile.display_name, profile["display_name"])

    def test_find_nonexisting_profile_by_name(self):
        client = Client()
        client.force_login(self.user_profile.user)

        name_part = 'noexisting'

        response = client.get(reverse('find_profile_by_name'), {'display_name_part': name_part})
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        self.assertEqual(0, len(parsed["response"]))

    def test_find_profile_by_short_name(self):
        client = Client()
        client.force_login(self.user_profile.user)

        name_part = self.user_profile.display_name[:3]

        response = client.get(reverse('find_profile_by_name'), {'display_name_part': name_part})
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_INVALID_ARGUMENT)

    def test_find_all_profiles(self):
        client = Client()
        client.force_login(self.user_profile.user)

        response = client.get(reverse('find_profile_by_name'))
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        self.assertEqual(1, len(parsed["response"]))
        profile = parsed["response"][0]

        self.assertEqual(self.user_profile.user.id, profile["user_id"])
        self.assertEqual(self.user_profile.display_name, profile["display_name"])

    def test_update_profile_picture(self):
        client = Client()
        client.force_login(self.user_profile.user)

        filename = os.path.join(TEST_FILES_DIR, 'avatar.jpg')
        print(filename)
        with open(filename, "rb") as file:
            response = client.post(reverse('update_profile_picture'),
                                   json.dumps({'name': 'test avatar',
                                               'image': str(base64.encodebytes(file.read()))
                                               }),
                                   content_type='application/json')
        print(response)
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)

        response = client.get(reverse('get_profile'), json.dumps({'user_id': self.user_profile.user.id}),
                              content_type='application/json')
        parsed = self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
        profile = parsed["response"]

        self.assertEqual(profile['pic'], "{uid}_avatar.jpg".format(uid=self.user_profile.user.id))

    def test_upload_profile_confirmation(self):
        client = Client()
        client.force_login(self.user_profile.user)

        filename = os.path.join(TEST_FILES_DIR, 'confirmation.jpg')
        with open(filename, "rb") as file:
            response = client.post(reverse('upload_profile_confirmation'),
                                   {'name': 'test confirmation', 'image': file})
        self.parseAndCheckResponseCode(response, ResponseCode.RESPONSE_OK)
