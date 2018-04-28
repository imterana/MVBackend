from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_GET, require_POST

from ..misc.http_decorators import require_arguments
from ..misc.response import (
    APIInvalidArgumentResponse,
    APIResponse,
)
from ..models import UserProfile


def get_profile_by_uuid(uuid):
    try:
        profile = UserProfile.user.objects.filter(uuid=uuid).first()
    except ValidationError:
        profile = None
    return profile


@require_arguments(["user_id"])
@require_GET
@login_required
def profile_get(request):
    uuid = request.GET["user_id"]
    profile = get_profile_by_uuid(uuid=uuid)
    if profile is None:
        return APIInvalidArgumentResponse(error_msg="User profile does not exist")
    return APIResponse(response={"display_name": profile.username,
                                 "pic": profile.picture,
                                 "confirmed": profile.confirmed,
                                 "bio": profile.bio,
                                 "karma": profile.karma})


@require_arguments(["image"])
@require_POST
@login_required
def profile_update_picture(request):
    user = request.user
    # here will be dragons later
    return APIResponse()


@require_POST
@login_required
def profile_update_info(request):
    user = request.user
    if 'display_name' in request.POST:
        user.username = request.POST['display_name']
    if 'bio' in request.POST:
        user.bio = request.POST['bio']
    user.save()
    return APIResponse()


@require_arguments(["image"])
@require_POST
@login_required
def profile_confirm(request):
    # here will be dragons later
    return APIResponse()


@require_arguments(["display_name_part"])
@require_GET
def profile_find_by_name(request):
    if 'display_name_part' in request.GET:
        name = request.GET['display_name_part']
        if len(name) < 3:
            return APIInvalidArgumentResponse(error_msg="Name part is too short")
        query = UserProfile.user.objects.filter(username__icontains=name)
    else:
        query = UserProfile.user.objects.all()

    profiles = [{"user_id": profile.user.uuid,
                 "display_name": profile.user.username}
                for profile in query]

    return APIResponse(response=profiles)
