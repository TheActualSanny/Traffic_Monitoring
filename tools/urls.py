from . import views
from django.urls import path

app_name = 'tools'

urlpatterns = [
    path('', views.add_mac, name = 'add-mac'),
    path('remove/', views.remove_target, name = 'remove-mac'),
    path('start/', views.invoke_sniffer, name = 'invoke-sniffer'),
    path('terminate/', views.terminate_sniffer, name = 'terminate-sniffer'),
    path('update/', views.get_networkifc, name = 'interface-name'),
    path('packets/', views.get_packets, name = 'get-packets'),
    path('lookups/', views.lookup_page, name = 'lookups'),
    path('initiate/', views.initiate_lookups, name = 'initiate-lookups'),
    path('lookup_records/', views.get_lookups, name = 'get-lookups'),
    path('loadmacs/', views.get_macs, name = 'get-macs'),
    path('managemac/', views.manage_target, name = 'select-mac')
]