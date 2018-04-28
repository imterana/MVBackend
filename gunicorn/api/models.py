from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    picture = models.CharField(unique=True)
    confirmed = models.BooleanField(default=False)
    bio = models.CharField(max_length=128)
    karma = models.PositiveIntegerField(default=0)
