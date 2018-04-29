from django.urls import path

from . import views

urlpatterns = [
    path('GetProfile', views.profile_get, name='get_profile'),
    path('UpdateProfilePicture', views.profile_update_picture, name='update_profile_picture'),
    path('UpdateProfileInfo', views.profile_update_info, name='update_profile_info'),
    path('UploadProfileConfirmation', views.profile_confirm, name='upload_profile_confirmation'),
    path('FindByName', views.profile_find_by_name, name='find_profile_by_name'),
]
