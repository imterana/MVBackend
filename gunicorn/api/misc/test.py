from django.test import TestCase

import json


class APITestCase(TestCase):
    def parseAndCheckResponseCode(self, response, code):
        self.assertEqual(200, response.status_code)
        parsed = json.loads(response.content)
        self.assertEqual(code, parsed["error"])
        return parsed
