from .views import TrafficMonitoring
from django.urls import path

app_name = 'tools'

urlpatterns = [
    path('tools/', TrafficMonitoring.add_mac, name = 'add-mac'),
    path('remove/', TrafficMonitoring.remove_target, name = 'remove-mac'),
    path('start/', TrafficMonitoring.invoke_sniffer, name = 'invoke-sniffer'),
    path('terminate/', TrafficMonitoring.terminate_sniffer, name = 'terminate-sniffer'),
    path('update/', TrafficMonitoring.get_networkifc, name = 'interface-name'),
    path('loadmacs/', TrafficMonitoring.get_macs, name = 'get-macs'),
    path('managemac/', TrafficMonitoring.manage_target, name = 'select-mac')
]