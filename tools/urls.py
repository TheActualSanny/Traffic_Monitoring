from . import views
from django.urls import path

app_name = 'tools'

urlpatterns = [
    path('', views.add_mac, name = 'add-mac'),
    path('remove/', views.remove_target, name = 'remove-mac'),
    path('start/', views.invoke_sniffer, name = 'invoke-sniffer'),
    path('terminate/', views.terminate_sniffer, name = 'terminate-sniffer'),
    path('update/', views.get_networkifc, name = 'interface-name')
]