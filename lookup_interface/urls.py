from . import views
from django.urls import path

app_name = 'lookup_interface'

urlpatterns = [
    path('lookup_page/', views.lookup_page, name = 'lookups'),
    path('initiate/', views.initiate_lookups, name = 'initiate-lookups')
]