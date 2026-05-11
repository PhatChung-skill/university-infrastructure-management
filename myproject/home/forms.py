import re

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.core.exceptions import ValidationError
from .models import Maintenance, Incident, QuickIncidentReport, IncidentType, AppUser


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


def _validate_school_email_for_reset(email: str) -> str:
    """Email trường + đã đồng bộ User/AppUser (dùng cho quên mật khẩu)."""
    from django.contrib.auth import get_user_model

    email = (email or "").strip()
    if not email:
        raise ValidationError("Vui lòng nhập email.")
    el = email.lower()
    if "@" not in el:
        raise ValidationError("Email không hợp lệ.")
    domain = el.rsplit("@", 1)[-1]

    allowed_domains = getattr(settings, "SCHOOL_EMAIL_ALLOWED_DOMAINS", None)
    suffixes = getattr(settings, "SCHOOL_EMAIL_DOMAIN_SUFFIXES", (".edu.vn",))

    if allowed_domains:
        if domain not in allowed_domains:
            ex = allowed_domains[0]
            raise ValidationError(
                "Chỉ chấp nhận email trường theo danh sách đã cấu hình. "
                f"Ví dụ: mã_số@{ex}"
            )
    elif not any(domain.endswith(suf) for suf in suffixes):
        raise ValidationError(
            "Chỉ chấp nhận email thuộc tên miền trường. "
            f"Các đuôi được phép: {', '.join(suffixes)}."
        )

    if not AppUser.objects.filter(email__iexact=el).exists():
        raise ValidationError("Không có tài khoản nào khớp với email này trong hệ thống.")

    User = get_user_model()
    synced = False
    for au in AppUser.objects.filter(email__iexact=el):
        if User.objects.filter(
            username__iexact=au.username, email__iexact=el, is_active=True
        ).exists():
            synced = True
            break
    if not synced:
        raise ValidationError(
            "Email đã có trong hệ thống nhưng chưa khớp tài khoản đăng nhập. "
            "Vui lòng liên hệ quản trị viên để kiểm tra đồng bộ email."
        )
    return el


def validate_app_user_email_domain(email: str) -> str:
    """Email người dùng (AppUser): chỉ domain được cấu hình (vd. @hcmunre.edu.vn)."""
    email = (email or "").strip()
    if not email:
        raise ValidationError("Vui lòng nhập email.")
    el = email.lower()
    if "@" not in el:
        raise ValidationError("Email không hợp lệ.")
    domain = el.rsplit("@", 1)[-1]
    allowed_domains = getattr(settings, "SCHOOL_EMAIL_ALLOWED_DOMAINS", None)
    suffixes = getattr(settings, "SCHOOL_EMAIL_DOMAIN_SUFFIXES", (".edu.vn",))
    if allowed_domains:
        if domain not in allowed_domains:
            ex = allowed_domains[0]
            raise ValidationError(
                f"Chỉ chấp nhận email có đuôi @{ex}."
            )
    elif not any(domain.endswith(suf) for suf in suffixes):
        raise ValidationError(
            "Chỉ chấp nhận email thuộc tên miền trường. "
            f"Các đuôi được phép: {', '.join(suffixes)}."
        )
    return el


class ForgotPasswordEmailForm(forms.Form):
    """Bước 1: nhập email trường — hệ thống gửi mã 6 số."""

    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "ten@hcmunre.edu.vn",
                "autocomplete": "email",
            }
        ),
    )

    def clean_email(self):
        return _validate_school_email_for_reset(self.cleaned_data.get("email"))


class VerifySixDigitForm(forms.Form):
    """Bước 2: nhập mã 6 số từ email."""

    code = forms.CharField(
        label="Mã xác nhận",
        max_length=12,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg text-center letter-spacing-code",
                "placeholder": "000000",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "pattern": r"[0-9]{6}",
                "maxlength": "6",
                "spellcheck": "false",
            }
        ),
    )

    def clean_code(self):
        raw = (self.cleaned_data.get("code") or "").strip().replace(" ", "")
        if not re.fullmatch(r"\d{6}", raw):
            raise ValidationError("Nhập đúng 6 chữ số.")
        return raw


class BootstrapSetPasswordForm(SetPasswordForm):
    """Form đặt lại mật khẩu — giao diện Bootstrap giống trang đăng nhập."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "Mật khẩu mới"
        self.fields["new_password2"].label = "Xác nhận mật khẩu mới"
        self.fields["new_password1"].widget.attrs.setdefault("class", "form-control")
        self.fields["new_password1"].widget.attrs.setdefault("placeholder", "Mật khẩu mới")
        self.fields["new_password2"].widget.attrs.setdefault("class", "form-control")
        self.fields["new_password2"].widget.attrs.setdefault("placeholder", "Nhập lại mật khẩu mới")


class BootstrapPasswordChangeForm(PasswordChangeForm):
    """Form đổi mật khẩu khi người dùng đã đăng nhập."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Mật khẩu cũ"
        self.fields["new_password1"].label = "Mật khẩu mới"
        self.fields["new_password2"].label = "Xác nhận mật khẩu mới"
        self.fields["old_password"].widget.attrs.setdefault("class", "form-control")
        self.fields["old_password"].widget.attrs.setdefault("placeholder", "Nhập mật khẩu cũ")
        self.fields["new_password1"].widget.attrs.setdefault("class", "form-control")
        self.fields["new_password1"].widget.attrs.setdefault("placeholder", "Nhập mật khẩu mới")
        self.fields["new_password2"].widget.attrs.setdefault("class", "form-control")
        self.fields["new_password2"].widget.attrs.setdefault("placeholder", "Nhập lại mật khẩu mới")


class FacilityIncidentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)
        self.fields["asset"].help_text = (
            "Chọn đúng thiết bị hoặc cây trong danh sách. Hệ thống tự gắn vị trí (tòa / tầng / phòng "
            "hoặc tọa độ cây) — không cần chọn thêm trên bản đồ."
        )
        # Giữ đủ queryset (lọc hiển thị do JS); tránh lỗi khi POST không khớp tạm thời.
        self.fields["incident_type"].queryset = IncidentType.objects.all().order_by("name")
        self.fields["incident_type"].help_text = (
            "Danh sách tự lọc theo tài sản: thiết bị → loại áp dụng cho thiết bị hoặc an ninh; "
            "cây → loại áp dụng cho cây xanh hoặc an ninh."
        )

    def clean(self):
        cleaned = super().clean()
        asset = cleaned.get("asset")
        incident_type = cleaned.get("incident_type")
        if asset and incident_type:
            allowed = {asset.asset_type, "security"}
            applies = set(incident_type.applies_to or [])
            if not applies.intersection(allowed):
                self.add_error(
                    "incident_type",
                    "Loại sự cố không phù hợp với tài sản: thiết bị chỉ chọn loại (thiết bị / an ninh); "
                    "cây chỉ chọn loại (cây xanh / an ninh).",
                )
        return cleaned

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


class TeacherQuickIncidentReportForm(forms.Form):
    """
    Báo cáo sự cố nhanh dạng text (giảng viên gửi tới CSVC).
    """

    message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Nhập nội dung báo cáo sự cố nhanh...",
            }
        ),
        label="Nội dung báo cáo",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_bootstrap(self)