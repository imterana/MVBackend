from django.urls import path

from . import views

urlpatterns = [
        path('CreateEvent', views.event_create, name='create_event'),
        path('GetEvents', views.event_list, name='get_events'),
        path('JoinEvent', views.event_join, name='join_event'),
        path('LeaveEvent', views.event_leave, name='leave_event'),
        path('DeleteEvent', views.event_delete, name='delete_event'),
        path('GetCreatedEvents', views.created_events_for_user,
             name='get_created_events'),
        path('GetJoinedEvents', views.joined_events_for_user,
             name='get_joined_events'),
]
