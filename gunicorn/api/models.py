import uuid
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


class Event(models.Model):
    creator = models.ForeignKey(User, related_name='creator_of',
                                on_delete=models.CASCADE)
    name = models.CharField(max_length=32, unique=True)
    users = models.ManyToManyField(User)
    uuid = models.UUIDField(primary_key=True,
                            default=uuid.uuid4, editable=False)
    time_from = models.DateTimeField(default=datetime.utcnow)
    time_to = models.DateTimeField(default=datetime.utcnow)
