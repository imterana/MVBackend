from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    display_name = models.CharField(max_length=128)
    picture = models.CharField(max_length=128, default=None)
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
    time_from = models.DateTimeField(default=datetime.utcnow)
    time_to = models.DateTimeField(default=datetime.utcnow)


# create user profile automatically on creating new user
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
                user=instance,
                display_name=instance.username,
                picture="https://i.imgur.com/erdtqth.jpg",
        )
