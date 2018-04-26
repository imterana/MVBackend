from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.decorators.http import require_GET, require_POST

from ..models import Event
from ..misc.http_decorators import require_arguments
from ..misc.response import (
        APIInvalidArgumentResponse,
        APINotPermittedResponse,
        APIResponse,
        APIUnknownErrorResponse,
)


def get_event_by_uuid(uuid):
    try:
        event = Event.objects.filter(uuid=uuid).first()
    except ValidationError:
        event = None
    return event


@require_arguments(["name"])
@require_POST
@login_required
def event_create(request):
    name = request.POST["name"]
    user = request.user
    try:
        event = Event(name=name, creator=user)
        event.users.set([user])
        event.save()
    except IntegrityError:
        return APIUnknownErrorResponse(error_msg="Could not create new event")
    return APIResponse(response={"event_id": event.uuid})


@require_GET
def event_list(request):
    events = []
    for event in Event.objects.all():
        events.append({"name": event.name,
                       "event_id": event.uuid})
    return APIResponse(response=events)


@require_arguments(["event_id"])
@require_POST
@login_required
def event_join(request):
    uuid = request.POST["event_id"]
    user = request.user
    event = get_event_by_uuid(uuid)
    if event is None:
        return APIInvalidArgumentResponse(error_msg="Event does not exist")
    if user in event.users.all():
        return APINotPermittedResponse(error_msg="Already joined the event")
    event.users.add(user)
    return APIResponse()


@require_arguments(["event_id"])
@require_POST
@login_required
def event_leave(request):
    uuid = request.POST["event_id"]
    user = request.user
    event = get_event_by_uuid(uuid)
    if event is None:
        return APIInvalidArgumentResponse(error_msg="Event does not exist")
    elif user not in event.users.all():
        return APINotPermittedResponse(error_msg="You are not in the event")
    event.users.remove(user)
    return APIResponse()


@require_arguments(["event_id"])
@require_POST
@login_required
def event_delete(request):
    uuid = request.POST["event_id"]
    user = request.user
    event = get_event_by_uuid(uuid)
    if event is None:
        return APIInvalidArgumentResponse(error_msg="Event does not exist")
    elif event.creator != user:
        return APINotPermittedResponse(error_msg="Only the creator can delete "
                                                 "the event")
    event.delete()
    return APIResponse()


@require_GET
@login_required
def joined_events_for_user(request):
    user = request.user
    events = []
    for event in Event.objects.filter(users__in=[user]):
        events.append({"name": event.name,
                       "creator": event.creator == user,
                       "event_id": event.uuid})
    return APIResponse(response=events)


@require_GET
@login_required
def created_events_for_user(request):
    user = request.user
    events = []
    for event in Event.objects.filter(creator=user):
        events.append({"name": event.name,
                       "event_id": event.uuid})
    return APIResponse(response=events)
