from django.urls import path

from . import views

urlpatterns = [
    path('GetCurrentUserId', views.get_current_user_id, name='get_current_user_id')
]
