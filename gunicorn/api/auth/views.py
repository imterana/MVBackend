from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

from ..misc.response import (
    APIResponse,
)


@require_GET
@login_required
def get_current_user_id(request):
    user = request.user
    return APIResponse(response={'user_id': user.id})
