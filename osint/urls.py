from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('lookups_api.urls')),
    path('', include('tools.urls')),
    path('authenticate/', include('user_authentication.urls', namespace = 'authentication')),
    path('lookups/', include('lookup_interface.urls', namespace = 'lookup_interface'))
]
