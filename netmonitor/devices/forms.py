from django import forms

from .models import Device


class DeviceReviewForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["hostname", "device_type", "vendor", "notes", "trusted"]
        widgets = {
            "hostname": forms.TextInput(attrs={"placeholder": "e.g. Dave's laptop"}),
            "vendor": forms.TextInput(attrs={"placeholder": "Optional manufacturer"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Optional notes"}),
        }
        labels = {
            "hostname": "Device name",
            "trusted": "Add this device to known devices",
        }
