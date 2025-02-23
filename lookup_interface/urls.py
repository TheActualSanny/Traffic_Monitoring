from .views import LookupInterface
from django.urls import path

app_name = 'lookup_interface'

urlpatterns = [
    path('lookup_page/', LookupInterface.lookup_page, name = 'lookups'),
    path('initiate/', LookupInterface.initiate_lookups, name = 'initiate-lookups')
]