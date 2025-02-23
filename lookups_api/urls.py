from . import views
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

app_name = 'lookups_api'

urlpatterns = [
    path('', views.LookupAPI.as_view(), name = 'lookup-api'),
    path('key', views.KeyView.as_view(), name = 'send_key')
]