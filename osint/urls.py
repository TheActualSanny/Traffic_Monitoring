from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('lookups_api.urls')),
    path('', include('tools.urls'))
]
