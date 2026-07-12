from django.urls import path

from . import views

urlpatterns = [
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('scan/', views.run_network_scan, name='run_network_scan'),
    path('monitoring/toggle/', views.toggle_auto_scan, name='toggle_auto_scan'),
    path('devices/<int:device_id>/', views.review_device, name='review_device'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
]
