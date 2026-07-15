from django.contrib import admin

from .models import Device, UserActivity


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
	list_display = ("hostname", "ip_address", "mac_address", "trusted", "online", "device_type")
	search_fields = ("hostname", "ip_address", "mac_address", "vendor")
	list_filter = ("trusted", "online", "device_type")


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
	list_display = ("timestamp", "user", "ip_address", "path", "method", "action")
	search_fields = ("user__username", "ip_address", "path", "action", "details")
	list_filter = ("method",)
	readonly_fields = ("timestamp", "user", "ip_address", "path", "method", "action", "details", "user_agent")
	ordering = ("-timestamp",)
