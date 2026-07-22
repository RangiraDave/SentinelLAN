from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from alerts.models import Alert
from scanner.models import MonitoringSettings
from scanner.scan_manager import run_scan

from .forms import DeviceReviewForm
from .models import Device, UserActivity


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


def _get_dashboard_context(request):
    known_devices = Device.objects.filter(trusted=True).order_by("-online", "-last_seen")
    discovered_devices = Device.objects.filter(trusted=False, dismissed=False).order_by("-first_seen", "-last_seen")
    unresolved_alerts = Alert.objects.filter(resolved=False).select_related("device")
    recent_activities = UserActivity.objects.select_related("user").order_by("-timestamp")[:50]
    return {
        "known_devices": known_devices,
        "discovered_devices": discovered_devices,
        "alerts": unresolved_alerts.order_by("-created_at")[:8],
        "known_count": known_devices.count(),
        "discovered_count": discovered_devices.count(),
        "recent_discovered_devices": discovered_devices[:3],
        "online_count": Device.objects.filter(online=True).count(),
        "new_device_alert_count": unresolved_alerts.filter(alert_type="NEW_DEVICE").count(),
        "total_count": Device.objects.count(),
        "recent_activities": recent_activities,
    }


@login_required
def dashboard(request):
    context = _get_dashboard_context(request)
    context["monitoring"] = MonitoringSettings.get_solo()
    return render(request, "devices/dashboard.html", context)


@login_required
def known_devices(request):
    known_devices = Device.objects.filter(trusted=True).order_by("-online", "-last_seen")
    search_query = (request.GET.get("search") or "").strip()
    device_type = (request.GET.get("device_type") or "").strip()

    if search_query:
        known_devices = known_devices.filter(
            models.Q(hostname__icontains=search_query)
            | models.Q(ip_address__icontains=search_query)
            | models.Q(mac_address__icontains=search_query)
            | models.Q(vendor__icontains=search_query)
        )

    if device_type:
        known_devices = known_devices.filter(device_type=device_type)

    unresolved_alerts = Alert.objects.filter(resolved=False).select_related("device")
    recent_activities = UserActivity.objects.select_related("user").order_by("-timestamp")[:50]
    context = {
        "known_devices": known_devices,
        "monitoring": MonitoringSettings.get_solo(),
        "alerts": unresolved_alerts.order_by("-created_at")[:8],
        "new_device_alert_count": unresolved_alerts.filter(alert_type="NEW_DEVICE").count(),
        "recent_activities": recent_activities,
        "known_count": known_devices.count(),
        "online_count": Device.objects.filter(online=True).count(),
        "search_query": search_query,
        "device_type": device_type,
        "device_types": Device.DEVICE_TYPES,
    }
    return render(request, "devices/known_devices.html", context)


@login_required
def discovered_devices(request):
    show_dismissed = request.GET.get("show") == "dismissed"
    discovered_devices = Device.objects.filter(
        trusted=False,
        dismissed=show_dismissed,
    ).order_by("-first_seen", "-last_seen")
    search_query = (request.GET.get("search") or "").strip()
    device_type = (request.GET.get("device_type") or "").strip()

    if search_query:
        discovered_devices = discovered_devices.filter(
            models.Q(hostname__icontains=search_query)
            | models.Q(ip_address__icontains=search_query)
            | models.Q(mac_address__icontains=search_query)
            | models.Q(vendor__icontains=search_query)
        )

    if device_type:
        discovered_devices = discovered_devices.filter(device_type=device_type)

    unresolved_alerts = Alert.objects.filter(resolved=False).select_related("device")
    recent_activities = UserActivity.objects.select_related("user").order_by("-timestamp")[:50]
    context = {
        "discovered_devices": discovered_devices,
        "monitoring": MonitoringSettings.get_solo(),
        "alerts": unresolved_alerts.order_by("-created_at")[:8],
        "new_device_alert_count": unresolved_alerts.filter(alert_type="NEW_DEVICE").count(),
        "recent_activities": recent_activities,
        "discovered_count": discovered_devices.count(),
        "online_count": Device.objects.filter(online=True).count(),
        "search_query": search_query,
        "device_type": device_type,
        "device_types": Device.DEVICE_TYPES,
        "show_dismissed": show_dismissed,
        "dismissed_count": Device.objects.filter(trusted=False, dismissed=True).count(),
    }
    return render(request, "devices/discovered_devices.html", context)


@login_required
@require_POST
def approve_device(request, device_id):
    device = get_object_or_404(Device, pk=device_id)
    device.trusted = True
    device.dismissed = False
    device.save(update_fields=["trusted", "dismissed"])
    messages.success(request, f"{device.hostname or device.ip_address} is now a known device.")
    return redirect("discovered_devices")


@login_required
@require_POST
def ignore_device(request, device_id):
    device = get_object_or_404(Device, pk=device_id)
    device.dismissed = True
    device.trusted = False
    device.save(update_fields=["dismissed", "trusted"])
    messages.success(request, f"{device.hostname or device.ip_address} was dismissed. You can restore it from Dismissed devices.")
    return redirect("discovered_devices")


@login_required
@require_POST
def restore_device(request, device_id):
    device = get_object_or_404(Device, pk=device_id, trusted=False)
    device.dismissed = False
    device.save(update_fields=["dismissed"])
    messages.success(request, f"{device.hostname or device.ip_address} was returned to the review queue.")
    return redirect("discovered_devices")


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
        if isinstance(scan_results, tuple):
            new_devices, updated_devices = scan_results
            discovered_count = len(new_devices) + len(updated_devices)
        else:
            discovered_count = len(scan_results or [])

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"discovered": discovered_count})
        messages.success(request, f"Scan complete: {discovered_count} device(s) discovered.")
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
    return_page = request.POST.get("return_to") or request.GET.get("next")
    if return_page not in {"dashboard", "discovered_devices", "known_devices"}:
        return_page = "dashboard"
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
        return redirect(return_page)

    unresolved_alerts = Alert.objects.filter(resolved=False).select_related("device")
    recent_activities = UserActivity.objects.select_related("user").order_by("-timestamp")[:50]
    context = {
        "device": device,
        "form": form,
        "monitoring": MonitoringSettings.get_solo(),
        "alerts": unresolved_alerts.order_by("-created_at")[:8],
        "new_device_alert_count": unresolved_alerts.filter(alert_type="NEW_DEVICE").count(),
        "recent_activities": recent_activities,
        "return_page": return_page,
    }
    return render(request, "devices/review_device.html", context)


@login_required
@require_POST
def resolve_alert(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)
    alert.resolved = True
    alert.save(update_fields=["resolved"])
    return redirect("dashboard")


@login_required
@require_POST
def clear_all_alerts(request):
    Alert.objects.filter(resolved=False).update(resolved=True)
    return redirect("dashboard")
