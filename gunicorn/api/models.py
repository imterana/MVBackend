from django.db import models
from django.contrib.auth.models import User

import uuid


class Event(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    users = models.ManyToManyField(User)
    uuid = models.UUIDField(primary_key=True,
                            default=uuid.uuid4, editable=False)
