from django.db import models
from django.conf import settings


class Device(models.Model):
    DEVICE_TYPES = [
        ("unknown", "Unknown"),
        ("computer", "Computer"),
        ("phone", "Phone"),
        ("tablet", "Tablet"),
        ("router", "Router"),
        ("printer", "Printer"),
        ("camera", "Camera"),
        ("smart_home", "Smart-home device"),
        ("other", "Other"),
    ]

    hostname = models.CharField(max_length=255, blank=True)

    ip_address = models.GenericIPAddressField(
        unique=True
    )

    mac_address = models.CharField(
        max_length=17,
    )

    vendor = models.CharField(
        max_length=255,
        blank=True
    )

    device_type = models.CharField(
        max_length=30,
        choices=DEVICE_TYPES,
        default="unknown",
    )

    first_seen = models.DateTimeField(
        auto_now_add=True
    )

    last_seen = models.DateTimeField(
        auto_now=True
    )

    trusted = models.BooleanField(
        default=False
    )

    online = models.BooleanField(
        default=True
    )

    notes = models.TextField(
        blank=True
    )

    def __str__(self):
        return f"{self.hostname or self.ip_address} ({self.mac_address})"


class UserActivity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp.isoformat()} {self.user} {self.action}"
