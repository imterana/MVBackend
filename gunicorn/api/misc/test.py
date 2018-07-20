import json

from django.test import Client
from django.test import TestCase
from django.urls import reverse


class APITestCase(TestCase):
    def parseAndCheckResponseCode(self, response, code):
        self.assertEqual(200, response.status_code)
        parsed = json.loads(response.content)
        self.assertEqual(code, parsed["error"])
        return parsed


class JSONClient(Client):
    def post_json(self, path, message):
        return self.post(path, json.dumps(message), content_type='application/json')
