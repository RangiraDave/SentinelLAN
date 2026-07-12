from django.db import models
from django.utils import timezone


class MonitoringSettings(models.Model):
    """Singleton configuration shared by the dashboard and monitor command."""

    auto_scan_enabled = models.BooleanField(default=False)
    scan_interval_seconds = models.PositiveIntegerField(default=60)
    last_scan_at = models.DateTimeField(blank=True, null=True)

    @classmethod
    def get_solo(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings

    def mark_scan_complete(self):
        self.last_scan_at = timezone.now()
        self.save(update_fields=["last_scan_at"])
