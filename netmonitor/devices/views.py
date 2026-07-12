from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from alerts.models import Alert
from scanner.scan_manager import run_scan

from .models import Device


def dashboard(request):
    devices = Device.objects.order_by("-online", "-last_seen")
    unresolved_alerts = Alert.objects.filter(resolved=False).select_related("device")
    return render(request, "devices/dashboard.html", {
        "devices": devices,
        "alerts": unresolved_alerts.order_by("-created_at")[:8],
        "device_count": devices.count(),
        "online_count": devices.filter(online=True).count(),
        "trusted_count": devices.filter(trusted=True).count(),
        "new_device_alert_count": unresolved_alerts.filter(alert_type="NEW_DEVICE").count(),
    })


@require_POST
def run_network_scan(request):
    try:
        scan_results = run_scan()
    except Exception as error:
        messages.error(request, f"Scan could not be completed: {error}")
    else:
        messages.success(request, f"Scan complete: {len(scan_results)} device(s) discovered.")
    return redirect("dashboard")


@require_POST
def resolve_alert(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)
    alert.resolved = True
    alert.save(update_fields=["resolved"])
    messages.success(request, "Alert marked as resolved.")
    return redirect("dashboard")
