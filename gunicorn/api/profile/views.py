import os
import base64

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_GET, require_POST

from ..misc.http_decorators import require_arguments, require_files, require_content_type
from ..misc.response import (
    APIInvalidArgumentResponse,
    APIResponse,
    APIMissingArgumentResponse
)
from ..models import UserProfile

AVATARS_DIR = '/usr/src/images/avatars/'
CONFIRMATIONS_DIR = '/usr/src/images/confirmations/'


def get_profile_by_id(user_id):
    try:
        profile = UserProfile.objects.filter(user__id=user_id).first()
    except (ValidationError, ValueError):
        profile = None
    return profile


def save_file(file, filename):
    with open(filename, 'wb+') as destination:
        destination.write(file)


@require_content_type('json')
@require_arguments(["user_id"])
@require_GET
@login_required
def profile_get(request):
    user_id = request.GET["user_id"]
    profile = get_profile_by_id(user_id=user_id)
    if profile is None:
        return APIInvalidArgumentResponse(error_msg="User profile does not exist")
    return APIResponse(response={"display_name": profile.display_name,
                                 "pic": profile.picture,
                                 "confirmed": profile.confirmed,
                                 "bio": profile.bio,
                                 "karma": profile.karma})


@require_content_type('json')
@require_arguments(["image", "name"])
@require_POST
@login_required
def profile_update_picture(request):
    print(request)
    user = request.user
    image_file = base64.decodebytes(request.POST["image"].encode('utf-8'))
    _, extension = os.path.splitext(request.POST["name"])
    filename = "{uid}_avatar{ext}".format(uid=user.id, ext=extension)
    save_file(image_file, os.path.join(AVATARS_DIR, filename))

    profile = UserProfile.objects.filter(user=user).first()
    profile.picture = filename
    profile.save()
    return APIResponse()


@require_content_type('json')
@require_POST
@login_required
def profile_update_info(request):
    if 'display_name' not in request.POST and 'bio' not in request.POST:
        return APIMissingArgumentResponse(error_msg="Bio or name are required")

    profile = UserProfile.objects.filter(user=request.user).first()
    if 'display_name' in request.POST:
        profile.display_name = request.POST['display_name']
    if 'bio' in request.POST:
        profile.bio = request.POST['bio']
    profile.save()
    return APIResponse()


@require_content_type('json')
@require_arguments(["image", "name"])
@require_POST
@login_required
def profile_add_confirmation_image(request):
    # TODO some notification for moderator to mark the user as confirmed
    user = request.user
    image_file = base64.decodebytes(request.POST["image"].encode('utf-8'))
    _, extension = os.path.splitext(request.POST["name"])
    filename = "{uid}_confirmation{ext}".format(uid=user.id, ext=extension)
    save_file(image_file, os.path.join(CONFIRMATIONS_DIR, filename))
    return APIResponse()


@require_content_type('json')
@require_GET
def profile_find_by_name(request):
    if 'display_name_part' in request.GET:
        name = request.GET['display_name_part']
        if len(name) < 4:
            return APIInvalidArgumentResponse(error_msg="Name part is too short")
        query = UserProfile.objects.filter(display_name__icontains=name)
    else:
        query = UserProfile.objects.all()

    profiles = [{"user_id": profile.user.id,
                 "display_name": profile.display_name}
                for profile in query]

    return APIResponse(response=profiles)
