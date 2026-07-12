from django.db import models


class Device(models.Model):
    hostname = models.CharField(max_length=255, blank=True)

    ip_address = models.GenericIPAddressField()

    mac_address = models.CharField(
        max_length=17,
        unique=True
    )

    vendor = models.CharField(
        max_length=255,
        blank=True
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