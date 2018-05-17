from django.urls import path

from .marking.consumers import MarkingConsumer

websocket_urlpatterns = [path("ws/marking", MarkingConsumer)]
