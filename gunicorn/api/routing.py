from django.urls import path

from .marking.consumers import MarkingConsumer, MarkMeConsumer

websocket_urlpatterns = [path("ws/marking", MarkingConsumer),
                         path("ws/mark_me", MarkMeConsumer)]
