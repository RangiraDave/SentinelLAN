from django.urls import path

from . import views

urlpatterns = [
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('known-devices/', views.known_devices, name='known_devices'),
    path('discovered-devices/', views.discovered_devices, name='discovered_devices'),
    path('devices/<int:device_id>/approve/', views.approve_device, name='approve_device'),
    path('devices/<int:device_id>/ignore/', views.ignore_device, name='ignore_device'),
    path('devices/<int:device_id>/restore/', views.restore_device, name='restore_device'),
    path('scan/', views.run_network_scan, name='run_network_scan'),
    path('monitoring/toggle/', views.toggle_auto_scan, name='toggle_auto_scan'),
    path('devices/<int:device_id>/', views.review_device, name='review_device'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('alerts/clear-all/', views.clear_all_alerts, name='clear_all_alerts'),
]
