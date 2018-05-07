from django.urls import path, include

urlpatterns = [
    path('profile/', include('api.profile.urls')),
    path('events/', include('api.events.urls')),
    path('auth/', include('api.auth.urls')),
]
