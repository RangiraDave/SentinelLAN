from django.db import models
from devices.models import Device


class Alert(models.Model):

    ALERT_TYPES = [
        ("NEW_DEVICE", "New Device"),
        ("DEVICE_OFFLINE", "Device Offline"),
        ("MAC_CHANGED", "MAC Changed"),
    ]

    alert_type = models.CharField(
        max_length=30,
        choices=ALERT_TYPES
    )

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    resolved = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.message