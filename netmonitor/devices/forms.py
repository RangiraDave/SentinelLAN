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
        help_texts = {
            "hostname": "Use a name you will recognize later, such as Kitchen printer.",
            "device_type": "Choose the closest match; you can change it later.",
            "vendor": "Optional. This may be the manufacturer shown on the device.",
            "notes": "Optional details that help you or another operator recognize it.",
            "trusted": "Only select this if you recognize and allow this device on your network.",
        }
