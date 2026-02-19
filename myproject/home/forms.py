from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Maintenance, Incident


def _apply_bootstrap(form: forms.Form) -> None:
    """
    Gắn class Bootstrap cho toàn bộ field để template chỉ cần {{ form.field }}.
    """
    for field in form.fields.values():
        widget = field.widget
        base_class = widget.attrs.get("class", "")

        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            cls = "form-select"
        elif isinstance(widget, forms.CheckboxInput):
            cls = "form-check-input"
        else:
            cls = "form-control"

        widget.attrs["class"] = f"{base_class} {cls}".strip()
class BootstrapAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên đăng nhập',
            'autofocus': 'autofocus',
        })
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mật khẩu',
        })
    )


class FacilityIncidentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)

    class Meta:
        model = Incident
        fields = [
            "asset",
            "incident_type",
            "priority",
            "title",
            "description",
        ]
        labels = {
            "asset": "Tài sản",
            "incident_type": "Loại sự cố",
            "priority": "Mức độ ưu tiên",
            "title": "Tiêu đề",
            "description": "Mô tả chi tiết",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Ví dụ: Máy chiếu phòng B204 không hoạt động"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Mô tả tình trạng, vị trí, biểu hiện lỗi...",
                }
            ),
        }

class FacilityMaintenanceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)

    class Meta:
        model = Maintenance
        fields = [
            "asset",
            "maintenance_type",
            "maintenance_date",
            "cost",
            "note",
        ]
        labels = {
            "asset": "Tài sản",
            "maintenance_type": "Loại bảo trì",
            "maintenance_date": "Ngày bảo trì",
            "cost": "Chi phí (VNĐ)",
            "note": "Ghi chú",
        }
        widgets = {
            "maintenance_date": forms.DateInput(attrs={"type": "date"}),
            "cost": forms.NumberInput(attrs={"placeholder": "Ví dụ: 1500000"}),
            "note": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Ghi chú thêm (nếu có)"}
            ),
        }