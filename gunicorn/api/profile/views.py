import os
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_GET, require_POST

from ..misc.http_decorators import require_arguments, require_files
from ..misc.response import (
    APIInvalidArgumentResponse,
    APIResponse,
)
from ..models import UserProfile

AVATARS_DIR = '/usr/src/avatars/'
CONFIRMATIONS_DIR = '/usr/src/confirmations/'


def get_profile_by_id(user_id):
    try:
        profile = UserProfile.objects.filter(user__id=user_id).first()
    except (ValidationError, ValueError):
        profile = None
    return profile


def save_file(file, directory):
    with open(os.path.join(directory, file.name), 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


@require_arguments(["user_id"])
@require_GET
@login_required
def profile_get(request):
    user_id = request.GET["user_id"]
    profile = get_profile_by_id(user_id=user_id)
    if profile is None:
        return APIInvalidArgumentResponse(error_msg="User profile does not exist")
    return APIResponse(response={"display_name": profile.user.username,
                                 "pic": profile.picture,
                                 "confirmed": profile.confirmed,
                                 "bio": profile.bio,
                                 "karma": profile.karma})


@require_files(["image"])
@require_POST
@login_required
def profile_update_picture(request):
    user = request.user
    image_file = request.FILES["image"]
    _, extension = os.path.splitext(image_file.name)
    image_file.name = user.username + extension
    save_file(image_file, AVATARS_DIR)
    return APIResponse()


@require_POST
@login_required
def profile_update_info(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if 'display_name' in request.POST:
        profile.user.username = request.POST['display_name']
    if 'bio' in request.POST:
        profile.bio = request.POST['bio']
    profile.user.save()
    profile.save()
    return APIResponse()


@require_files(["image"])
@require_POST
@login_required
def profile_confirm(request):
    user = request.user
    image_file = request.FILES["image"]
    _, extension = os.path.splitext(image_file.name)
    image_file.name = user.username + extension
    save_file(image_file, CONFIRMATIONS_DIR)
    return APIResponse()


@require_GET
def profile_find_by_name(request):
    if 'display_name_part' in request.GET:
        name = request.GET['display_name_part']
        if len(name) < 4:
            return APIInvalidArgumentResponse(error_msg="Name part is too short")
        query = UserProfile.objects.filter(user__username__icontains=name)
    else:
        query = UserProfile.objects.all()

    profiles = [{"user_id": profile.user.id,
                 "display_name": profile.user.username}
                for profile in query]

    return APIResponse(response=profiles)
