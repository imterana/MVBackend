from django.contrib.auth.decorators import login_required

from ..misc.response import (
    APIResponse,
)


@login_required
def get_current_user_id(request):
    user = request.user
    return APIResponse(response={'user_id': user.id})
