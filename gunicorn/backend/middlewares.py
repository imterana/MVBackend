import json


class JsonMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.content_type.lower() == 'application/json':
            request.json = json.loads(request.body)
        response = self.get_response(request)
        return response
