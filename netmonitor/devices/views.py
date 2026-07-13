from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from alerts.models import Alert
from scanner.models import MonitoringSettings
from scanner.scan_manager import run_scan

from .forms import DeviceReviewForm
from .models import Device


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return redirect("dashboard")
    return render(request, "devices/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect(request.POST.get("next") or "dashboard")
    return render(request, "devices/login.html", {"form": form, "next": request.GET.get("next", "")})


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    known_devices = Device.objects.filter(trusted=True).order_by("-online", "-last_seen")
    discovered_devices = Device.objects.filter(trusted=False).order_by("-last_seen")
    unresolved_alerts = Alert.objects.filter(resolved=False).select_related("device")
    monitoring = MonitoringSettings.get_solo()
    return render(request, "devices/dashboard.html", {
        "known_devices": known_devices,
        "discovered_devices": discovered_devices,
        "alerts": unresolved_alerts.order_by("-created_at")[:8],
        "known_count": known_devices.count(),
        "discovered_count": discovered_devices.count(),
        "online_count": Device.objects.filter(online=True).count(),
        "new_device_alert_count": unresolved_alerts.filter(alert_type="NEW_DEVICE").count(),
        "monitoring": monitoring,
    })


@login_required
@require_POST
def run_network_scan(request):
    try:
        scan_results = run_scan()
        MonitoringSettings.get_solo().mark_scan_complete()
    except Exception as error:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": str(error)}, status=500)
        messages.error(request, f"Scan could not be completed: {error}")
    else:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"discovered": len(scan_results)})
        messages.success(request, f"Scan complete: {len(scan_results)} device(s) discovered.")
    return redirect("dashboard")


@login_required
@require_POST
def toggle_auto_scan(request):
    monitoring = MonitoringSettings.get_solo()
    monitoring.auto_scan_enabled = request.POST.get("auto_scan") == "true"
    monitoring.save(update_fields=["auto_scan_enabled"])
    state = "enabled" if monitoring.auto_scan_enabled else "disabled"
    messages.success(request, f"Automatic scanning {state}.")
    return redirect("dashboard")


@login_required
@require_http_methods(["GET", "POST"])
def review_device(request, device_id):
    device = get_object_or_404(Device, pk=device_id)
    form = DeviceReviewForm(
        request.POST or None,
        instance=device,
        initial={
            "hostname": device.hostname or device.ip_address,
            "vendor": device.vendor or "",
            "device_type": device.device_type or "unknown",
        },
    )
    if request.method == "POST" and form.is_valid():
        device = form.save()
        if device.trusted:
            messages.success(request, f"{device.hostname or device.mac_address} is now a known device.")
        else:
            messages.success(request, "Device details updated.")
        return redirect("dashboard")
    return render(request, "devices/review_device.html", {"device": device, "form": form})


@login_required
@require_POST
def resolve_alert(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)
    alert.resolved = True
    alert.save(update_fields=["resolved"])
    messages.success(request, "Alert marked as resolved.")
    return redirect("dashboard")
