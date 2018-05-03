from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.decorators.http import require_GET, require_POST

from datetime import datetime

from .misc.time import datetime_to_string, datetime_from_string

from ..models import Event
from ..misc.http_decorators import require_arguments, cast_arguments
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


@cast_arguments({
    'time_from': datetime_from_string,
    'time_to': datetime_from_string
})
@require_arguments(["name", "time_from", "time_to"])
@require_POST
@login_required
def event_create(request):
    name = request.POST["name"]
    user = request.user
    time_from = request.POST["time_from"]
    time_to = request.POST["time_to"]
    if time_from > time_to:
        return APIInvalidArgumentResponse(
                error_msg="time_from comes after time_to")
    if time_from < datetime.utcnow():
        return APIInvalidArgumentResponse(error_msg="time_from has passed")
    try:
        event = Event(name=name,
                      creator=user,
                      time_from=time_from,
                      time_to=time_to)
        event.users.set([user])
        event.save()
    except IntegrityError:
        return APIUnknownErrorResponse(error_msg="Could not create new event")
    return APIResponse(response={"event_id": event.uuid})


@require_GET
def event_list(request):
    events = []
    if 'name' in request.GET:
        name = request.GET['name']
        if len(name) < 3:
            return APIInvalidArgumentResponse(error_msg="Name is too short")
        query = Event.objects.filter(name__icontains=name)
    else:
        query = Event.objects.all()

    for event in query:
        events.append({"name": event.name,
                       "event_id": event.uuid,
                       "time_from": datetime_to_string(event.time_from),
                       "time_to": datetime_to_string(event.time_to)})
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
    elif event.time_from < datetime.utcnow():
        return APINotPermittedResponse(error_msg="Event already began")
    elif event.time_to < datetime.utcnow():
        return APINotPermittedResponse(error_msg="Event already over")
    elif user in event.users.all():
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
    elif event.time_to < datetime.utcnow():
        return APINotPermittedResponse(error_msg="Event already over")
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
    elif event.time_from < datetime.utcnow():
        return APINotPermittedResponse(error_msg="Event has already started")
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
                       "event_id": event.uuid,
                       "time_from": datetime_to_string(event.time_from),
                       "time_to": datetime_to_string(event.time_to)}),
    return APIResponse(response=events)


@require_GET
@login_required
def created_events_for_user(request):
    user = request.user
    events = []
    for event in Event.objects.filter(creator=user):
        events.append({"name": event.name,
                       "event_id": event.uuid,
                       "time_from": datetime_to_string(event.time_from),
                       "time_to": datetime_to_string(event.time_to)})
    return APIResponse(response=events)
