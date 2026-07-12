import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from scanner.models import MonitoringSettings
from scanner.scan_manager import run_scan


class Command(BaseCommand):
    help = "Continuously runs enabled automatic network scans. Stop with Ctrl+C."

    def handle(self, *args, **options):
        self.stdout.write("NetWatch monitor started. Automatic scanning follows the dashboard setting.")
        while True:
            monitoring = MonitoringSettings.get_solo()
            scan_is_due = (
                monitoring.last_scan_at is None
                or (timezone.now() - monitoring.last_scan_at).total_seconds()
                >= monitoring.scan_interval_seconds
            )
            if monitoring.auto_scan_enabled and scan_is_due:
                try:
                    results = run_scan()
                    monitoring.mark_scan_complete()
                    self.stdout.write(self.style.SUCCESS(f"Scan complete: {len(results)} device(s) found."))
                except Exception as error:
                    self.stderr.write(self.style.ERROR(f"Scan failed: {error}"))
            time.sleep(5)
