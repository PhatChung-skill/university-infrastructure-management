"""
Forms for custom admin CRUD. Models with geom use lat/lng (or WKT for Building)
so templates can use a Leaflet map to set coordinates.
"""
from django import forms
from django.contrib.gis.geos import Point, GEOSGeometry
from .models import (
    Tree,
    Equipment,
    Room,
    Building,
    Incident,
    IncidentType,
    Asset,
    Maintenance,
    Role,
    AppUser,
)


def _add_bootstrap(form):
    for field in form.fields.values():
        widget = field.widget
        base = widget.attrs.get("class", "")
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            cls = "form-select"
        elif isinstance(widget, forms.CheckboxInput):
            cls = "form-check-input"
        else:
            cls = "form-control"
        widget.attrs["class"] = f"{base} {cls}".strip()


# ----- Tree (Point) -----
class TreeAdminForm(forms.ModelForm):
    latitude = forms.FloatField(
        required=False,
        label="Vĩ độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "placeholder": "10.7984"})
    )
    longitude = forms.FloatField(
        required=False,
        label="Kinh độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "placeholder": "106.6655"})
    )

    class Meta:
        model = Tree
        fields = ["code", "species", "height", "health_status", "planted_date", "last_trimmed", "note"]
        labels = {
            "code": "Mã cây",
            "species": "Loài cây",
            "height": "Chiều cao (m)",
            "health_status": "Tình trạng",
            "planted_date": "Ngày trồng",
            "last_trimmed": "Lần cắt tỉa gần nhất",
            "note": "Ghi chú",
        }
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "VD: T001"}),
            "species": forms.TextInput(attrs={"placeholder": "VD: Cây phượng"}),
            "planted_date": forms.DateInput(attrs={"type": "date"}),
            "last_trimmed": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        if self.instance and self.instance.pk and self.instance.geom:
            self.fields["latitude"].initial = self.instance.geom.y
            self.fields["longitude"].initial = self.instance.geom.x

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if lat is None or lng is None:
            self.add_error("latitude", "Vui lòng chọn vị trí trên bản đồ hoặc nhập tọa độ.")
            return cleaned
        cleaned["geom"] = Point(float(lng), float(lat), srid=4326)
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get("geom"):
            obj.geom = self.cleaned_data["geom"]
        if commit:
            obj.save()
        return obj


# ----- Equipment (Point + Room FK) -----
class EquipmentAdminForm(forms.ModelForm):
    latitude = forms.FloatField(required=False, label="Vĩ độ", widget=forms.NumberInput(attrs={"step": "0.000001"}))
    longitude = forms.FloatField(required=False, label="Kinh độ", widget=forms.NumberInput(attrs={"step": "0.000001"}))

    class Meta:
        model = Equipment
        fields = ["code", "name", "equipment_type", "status", "install_date", "last_maintenance", "room"]
        labels = {
            "code": "Mã thiết bị",
            "name": "Tên thiết bị",
            "equipment_type": "Loại thiết bị",
            "status": "Trạng thái",
            "install_date": "Ngày lắp đặt",
            "last_maintenance": "Lần bảo trì gần nhất",
            "room": "Phòng",
        }
        widgets = {
            "install_date": forms.DateInput(attrs={"type": "date"}),
            "last_maintenance": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        if self.instance and self.instance.pk and self.instance.geom:
            self.fields["latitude"].initial = self.instance.geom.y
            self.fields["longitude"].initial = self.instance.geom.x

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if lat is None or lng is None:
            self.add_error("latitude", "Vui lòng chọn vị trí trên bản đồ hoặc nhập tọa độ.")
            return cleaned
        cleaned["geom"] = Point(float(lng), float(lat), srid=4326)
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get("geom"):
            obj.geom = self.cleaned_data["geom"]
        if commit:
            obj.save()
        return obj


# ----- Room (Point + Building FK) -----
class RoomAdminForm(forms.ModelForm):
    latitude = forms.FloatField(required=False, label="Vĩ độ", widget=forms.NumberInput(attrs={"step": "0.000001"}))
    longitude = forms.FloatField(required=False, label="Kinh độ", widget=forms.NumberInput(attrs={"step": "0.000001"}))

    class Meta:
        model = Room
        fields = ["name", "room_type", "capacity", "building"]
        labels = {
            "name": "Tên phòng",
            "room_type": "Loại phòng",
            "capacity": "Sức chứa",
            "building": "Tòa nhà",
        }
        widgets = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        if self.instance and self.instance.pk and self.instance.geom:
            self.fields["latitude"].initial = self.instance.geom.y
            self.fields["longitude"].initial = self.instance.geom.x

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if lat is None or lng is None:
            self.add_error("latitude", "Vui lòng chọn vị trí trên bản đồ hoặc nhập tọa độ.")
            return cleaned
        cleaned["geom"] = Point(float(lng), float(lat), srid=4326)
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get("geom"):
            obj.geom = self.cleaned_data["geom"]
        if commit:
            obj.save()
        return obj


# ----- Building (Polygon - WKT) -----
class BuildingAdminForm(forms.ModelForm):
    geom_wkt = forms.CharField(
        required=False,
        label="Hình dạng (WKT Polygon)",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "POLYGON((106.665 10.798, 106.666 10.798, 106.666 10.799, 106.665 10.799, 106.665 10.798))"})
    )

    class Meta:
        model = Building
        fields = ["name", "description"]
        labels = {
            "name": "Tên tòa nhà",
            "description": "Mô tả",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        if self.instance and self.instance.pk and self.instance.geom:
            self.fields["geom_wkt"].initial = self.instance.geom.wkt

    def clean_geom_wkt(self):
        wkt = (self.cleaned_data.get("geom_wkt") or "").strip()
        if not wkt:
            if self.instance and self.instance.pk and self.instance.geom:
                return self.instance.geom
            raise forms.ValidationError("Vui lòng nhập WKT Polygon (hoặc vẽ trên bản đồ nếu có).")
        try:
            geom = GEOSGeometry(wkt, srid=4326)
            if geom.geom_type != "Polygon":
                raise forms.ValidationError("Chỉ chấp nhận POLYGON.")
            return geom
        except Exception as e:
            raise forms.ValidationError(f"WKT không hợp lệ: {e}")

    def save(self, commit=True):
        obj = super().save(commit=False)
        geom = self.cleaned_data.get("geom_wkt")
        if geom:
            obj.geom = geom
        if commit:
            obj.save()
        return obj


# ----- Incident (Point + Asset, IncidentType) -----
class IncidentAdminForm(forms.ModelForm):
    latitude = forms.FloatField(required=False, label="Vĩ độ", widget=forms.NumberInput(attrs={"step": "0.000001"}))
    longitude = forms.FloatField(required=False, label="Kinh độ", widget=forms.NumberInput(attrs={"step": "0.000001"}))

    class Meta:
        model = Incident
        fields = ["title", "description", "status", "priority", "asset", "incident_type"]
        labels = {
            "title": "Tiêu đề",
            "description": "Mô tả",
            "status": "Trạng thái",
            "priority": "Mức độ ưu tiên",
            "asset": "Tài sản",
            "incident_type": "Loại sự cố",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Tiêu đề sự cố"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        if self.instance and self.instance.pk and self.instance.geom:
            self.fields["latitude"].initial = self.instance.geom.y
            self.fields["longitude"].initial = self.instance.geom.x

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if lat is None or lng is None:
            self.add_error("latitude", "Vui lòng chọn vị trí trên bản đồ hoặc nhập tọa độ.")
            return cleaned
        cleaned["geom"] = Point(float(lng), float(lat), srid=4326)
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get("geom"):
            obj.geom = self.cleaned_data["geom"]
        if commit:
            obj.save()
        return obj


# ----- IncidentType (no geom) -----
class IncidentTypeAdminForm(forms.ModelForm):
    class Meta:
        model = IncidentType
        fields = ["code", "name", "description", "default_severity"]
        labels = {
            "code": "Mã loại sự cố",
            "name": "Tên loại sự cố",
            "description": "Mô tả",
            "default_severity": "Mức độ nghiêm trọng mặc định (1-5)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)


# ----- Asset (equipment OR tree + asset_type) -----
class AssetAdminForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["asset_type", "equipment", "tree"]
        labels = {
            "asset_type": "Loại tài sản",
            "equipment": "Thiết bị",
            "tree": "Cây xanh",
        }
        widgets = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)


# ----- Maintenance -----
class MaintenanceAdminForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = ["asset", "staff", "maintenance_type", "maintenance_date", "cost", "note"]
        labels = {
            "asset": "Tài sản",
            "staff": "Nhân viên phụ trách",
            "maintenance_type": "Loại bảo trì",
            "maintenance_date": "Ngày bảo trì",
            "cost": "Chi phí (VNĐ)",
            "note": "Ghi chú",
        }
        widgets = {
            "maintenance_date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)


# ----- Role -----
class RoleAdminForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ["name"]
        labels = {
            "name": "Tên vai trò",
        }
        widgets = {"name": forms.TextInput(attrs={"placeholder": "VD: Quản trị viên, Nhân viên CSVC"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)


# ----- AppUser -----
def _sync_appuser_to_django_user(app_user):
    """
    Tạo/cập nhật bản ghi User (Django auth) trùng username + mật khẩu
    để đăng nhập tại /login/ hoạt động.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user, created = User.objects.get_or_create(username=app_user.username)
    user.password = app_user.password  # cùng hash với AppUser
    user.is_active = True
    if app_user.role and app_user.role.name.lower() == "admin":
        user.is_staff = True
    else:
        user.is_staff = False
    user.save()


class AppUserAdminForm(forms.ModelForm):
    password_plain = forms.CharField(
        required=False,
        label="Mật khẩu (để trống nếu không đổi)",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )

    class Meta:
        model = AppUser
        fields = ["username", "role"]
        labels = {
            "username": "Tên đăng nhập",
            "role": "Vai trò",
        }
        widgets = {"username": forms.TextInput(attrs={"placeholder": "Tên đăng nhập"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        self.fields["password_plain"].widget.attrs.setdefault("class", "form-control")
        if not self.instance.pk:
            self.fields["password_plain"].required = True
            self.fields["password_plain"].label = "Mật khẩu"

    def save(self, commit=True):
        obj = super().save(commit=False)
        pwd = self.cleaned_data.get("password_plain")
        if pwd:
            from django.contrib.auth.hashers import make_password
            obj.password = make_password(pwd)
        if commit:
            obj.save()
            _sync_appuser_to_django_user(obj)
        return obj
