from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User

import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    display_name = models.CharField(max_length=128)
    picture = models.CharField(max_length=128, unique=True, default=None)
    confirmed = models.BooleanField(default=False)
    bio = models.CharField(max_length=128)
    karma = models.PositiveIntegerField(default=0)


class Event(models.Model):
    creator = models.ForeignKey(User, related_name='creator_of',
                                on_delete=models.CASCADE)
    name = models.CharField(max_length=32, unique=True)
    users = models.ManyToManyField(User)
    uuid = models.UUIDField(primary_key=True,
                            default=uuid.uuid4, editable=False)
