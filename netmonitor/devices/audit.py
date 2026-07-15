from .models import UserActivity


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")[:255]


def describe_request(request):
    resolver = getattr(request, "resolver_match", None)
    if not resolver:
        return f"{request.method} {request.path}"

    view_name = resolver.view_name or ""
    kwargs = resolver.kwargs or {}

    if view_name == "dashboard":
        return "Viewed dashboard"
    if view_name == "run_network_scan":
        return "Triggered network scan"
    if view_name == "toggle_auto_scan":
        action = "Enabled auto scan" if request.POST.get("auto_scan") == "true" else "Disabled auto scan"
        return action
    if view_name == "review_device":
        device_id = kwargs.get("device_id")
        return f"Reviewed device {device_id}" if request.method == "POST" else f"Viewed device review {device_id}"
    if view_name == "resolve_alert":
        alert_id = kwargs.get("alert_id")
        return f"Resolved alert {alert_id}"
    if view_name == "signup":
        return "Created account"
    if view_name == "login":
        return "Accessed login page" if request.method == "GET" else "Attempted login"
    if view_name == "logout":
        return "Logged out"

    return f"{request.method} {request.path}"


def log_user_activity(request, user=None, action=None, details=None):
    if user is None:
        user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return

    if action is None:
        action = describe_request(request)

    if details is None:
        if request.method == "GET":
            details = request.GET.urlencode()
        elif request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            details = "Form submission"
        else:
            details = ""

    UserActivity.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        path=request.path,
        method=request.method.upper(),
        action=action,
        details=details,
        user_agent=get_user_agent(request),
    )
