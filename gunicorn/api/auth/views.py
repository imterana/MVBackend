from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from ..misc.response import (
    APIResponse,
)


@require_GET
def get_current_user_id(request):
    user = request.user
    if user is None:
        return APIResponse(response={'user_id': None})
    return APIResponse(response={'user_id': user.id})
