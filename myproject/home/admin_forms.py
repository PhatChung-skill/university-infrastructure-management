"""
Forms for custom admin CRUD. Models with geom use lat/lng (or WKT for Building)
so templates can use a Leaflet map to set coordinates.
"""
from django import forms
from django.contrib.gis.geos import Point, GEOSGeometry, Polygon
import unicodedata
from .forms import validate_app_user_email_domain
from .models import (
    Tree,
    Equipment,
    Room,
    Building,
    UniversityBranch,
    Floor,
    Incident,
    IncidentType,
    Asset,
    Maintenance,
    Role,
    AppUser,
    AboutHeroSection,
    AboutCoreValue,
    AboutAnnouncement,
    AboutFeaturedEvent,
)


def _validate_polygon_vertices_non_negative(geom) -> None:
    """Mọi đỉnh đa giác WGS84: kinh độ (x) và vĩ độ (y) không được âm."""
    gtype = geom.geom_type
    if gtype == "Polygon":
        for i in range(len(geom)):
            ring = geom[i]
            for coord in ring.coords:
                x, y = float(coord[0]), float(coord[1])
                if x < 0 or y < 0:
                    raise forms.ValidationError(
                        "Tọa độ đỉnh (kinh độ, vĩ độ) không được âm."
                    )
    elif gtype == "MultiPolygon":
        for poly in geom:
            _validate_polygon_vertices_non_negative(poly)


class UniversityBranchAdminForm(forms.ModelForm):
    latitude = forms.FloatField(
        required=False,
        label="Vĩ độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0"}),
    )
    longitude = forms.FloatField(
        required=False,
        label="Kinh độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0"}),
    )
    address = forms.CharField(required=False, label="Địa chỉ", widget=forms.TextInput(attrs={"placeholder": "Nhập địa chỉ để tìm trên bản đồ"}))

    class Meta:
        model = UniversityBranch
        fields = ["name", "description"]
        labels = {"name": "Tên chi nhánh", "description": "Mô tả"}
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        if self.instance and self.instance.pk and self.instance.geom:
            center = self.instance.geom.centroid
            self.fields["latitude"].initial = center.y
            self.fields["longitude"].initial = center.x

    def clean(self):
        cleaned = super().clean()
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if lat is None or lng is None:
            # Allow save without map pin; keep existing geom if editing.
            cleaned["geom"] = self.instance.geom if self.instance and self.instance.pk else None
            return cleaned

        if lat < 0:
            self.add_error("latitude", "Vĩ độ không được âm.")
        if lng < 0:
            self.add_error("longitude", "Kinh độ không được âm.")
        if self.errors:
            return cleaned

        d = 0.00015
        cleaned["geom"] = Polygon.from_bbox((float(lng) - d, float(lat) - d, float(lng) + d, float(lat) + d))
        cleaned["geom"].srid = 4326
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get("geom"):
            obj.geom = self.cleaned_data["geom"]
        if commit:
            obj.save()
        return obj




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
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0", "placeholder": "10.7984"}),
    )
    longitude = forms.FloatField(
        required=False,
        label="Kinh độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0", "placeholder": "106.6655"}),
    )

    class Meta:
        model = Tree
        fields = ["code", "species", "height", "health_status", "planted_date", "last_trimmed", "note", "university_branch"]
        labels = {
            "code": "Mã cây",
            "species": "Loài cây",
            "height": "Chiều cao (m)",
            "health_status": "Tình trạng",
            "planted_date": "Ngày trồng",
            "last_trimmed": "Lần cắt tỉa gần nhất",
            "note": "Ghi chú",
            "university_branch": "Chi nhánh",
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
        if lat < 0:
            self.add_error("latitude", "Vĩ độ không được âm.")
        if lng < 0:
            self.add_error("longitude", "Kinh độ không được âm.")
        if self.errors:
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


# ----- Equipment (Point + Room FK + Indoor Local XY) -----
class EquipmentAdminForm(forms.ModelForm):
    university_branch = forms.ModelChoiceField(queryset=UniversityBranch.objects.all(), required=False, label="Chi nhánh")
    building = forms.ModelChoiceField(queryset=Building.objects.all(), required=False, label="Tòa nhà")
    floor = forms.ModelChoiceField(queryset=Floor.objects.all(), required=False, label="Tầng")
    latitude = forms.FloatField(
        required=False,
        label="Vĩ độ (Global)",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0"}),
    )
    longitude = forms.FloatField(
        required=False,
        label="Kinh độ (Global)",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0"}),
    )

    class Meta:
        model = Equipment
        fields = [
            "code", "name", "equipment_type", "status",
            "university_branch", "building", "floor",
            "install_date", "last_maintenance", "room",
            "local_x", "local_y",
        ]
        labels = {
            "code": "Mã thiết bị",
            "name": "Tên thiết bị",
            "equipment_type": "Loại thiết bị",
            "status": "Trạng thái",
            "university_branch": "Chi nhánh",
            "building": "Tòa nhà",
            "floor": "Tầng",
            "install_date": "Ngày lắp đặt",
            "last_maintenance": "Lần bảo trì gần nhất",
            "room": "Phòng",
            "local_x": "Tọa độ X trên sơ đồ (px)",
            "local_y": "Tọa độ Y trên sơ đồ (px)",
        }
        widgets = {
            "install_date": forms.DateInput(attrs={"type": "date"}),
            "last_maintenance": forms.DateInput(attrs={"type": "date"}),
            "local_x": forms.HiddenInput(),
            "local_y": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        self.fields["building"].queryset = Building.objects.select_related("university_branch").order_by("name")
        self.fields["floor"].queryset = Floor.objects.select_related("building").order_by("building__name", "level", "name")
        self.fields["room"].queryset = Room.objects.select_related("floor", "floor__building", "floor__building__university_branch").order_by("name")
        room_obj = self.instance.room if self.instance and self.instance.pk else None
        if room_obj and room_obj.floor:
            self.fields["floor"].initial = room_obj.floor
            self.fields["building"].initial = room_obj.floor.building
            self.fields["university_branch"].initial = room_obj.floor.building.university_branch
        posted_branch = self.data.get("university_branch")
        posted_building = self.data.get("building")
        posted_floor = self.data.get("floor")
        qs = self.fields["room"].queryset
        if posted_branch:
            qs = qs.filter(floor__building__university_branch_id=posted_branch)
        if posted_building:
            qs = qs.filter(floor__building_id=posted_building)
        if posted_floor:
            qs = qs.filter(floor_id=posted_floor)
        self.fields["room"].queryset = qs
        self.fields["room"].label_from_instance = lambda obj: (
            f"{obj.name} - {obj.floor.name if obj.floor else '-'} - "
            f"{obj.floor.building.name if obj.floor and obj.floor.building else '-'}"
        )
        if self.instance and self.instance.pk and self.instance.geom:
            self.fields["latitude"].initial = self.instance.geom.y
            self.fields["longitude"].initial = self.instance.geom.x

    def clean(self):
        cleaned = super().clean()
        branch = cleaned.get("university_branch")
        building = cleaned.get("building")
        floor = cleaned.get("floor")
        room = cleaned.get("room")
        if room:
            if floor and room.floor_id != floor.id:
                self.add_error("room", "Phòng không thuộc tầng đã chọn.")
            if building and (not room.floor or room.floor.building_id != building.id):
                self.add_error("room", "Phòng không thuộc tòa nhà đã chọn.")
            if branch and (not room.floor or not room.floor.building or room.floor.building.university_branch_id != branch.id):
                self.add_error("room", "Phòng không thuộc chi nhánh đã chọn.")
        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if lat is not None and lng is not None:
            coord_bad = False
            if lat < 0:
                self.add_error("latitude", "Vĩ độ không được âm.")
                coord_bad = True
            if lng < 0:
                self.add_error("longitude", "Kinh độ không được âm.")
                coord_bad = True
            if not coord_bad:
                cleaned["geom"] = Point(float(lng), float(lat), srid=4326)
        else:
            cleaned["geom"] = None
        lx, ly = cleaned.get("local_x"), cleaned.get("local_y")
        if lx is not None and float(lx) < 0:
            self.add_error("local_x", "Tọa độ X trên sơ đồ không được âm.")
        if ly is not None and float(ly) < 0:
            self.add_error("local_y", "Tọa độ Y trên sơ đồ không được âm.")
        if not room:
            cleaned["local_x"] = None
            cleaned["local_y"] = None
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if "geom" in self.cleaned_data:
            obj.geom = self.cleaned_data["geom"]
        if commit:
            obj.save()
        return obj


# ----- Room (Polygon + Floor FK) -----
class RoomAdminForm(forms.ModelForm):
    geom_wkt = forms.CharField(required=False, widget=forms.HiddenInput())
    latitude = forms.FloatField(
        required=False,
        label="Vĩ độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0"}),
    )
    longitude = forms.FloatField(
        required=False,
        label="Kinh độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0"}),
    )
    university_branch = forms.ModelChoiceField(queryset=UniversityBranch.objects.all(), required=False, label="Chi nhánh")
    building = forms.ModelChoiceField(queryset=Building.objects.all(), required=False, label="Tòa nhà (lọc tầng & bản đồ)")

    class Meta:
        model = Room
        fields = ["name", "room_type", "capacity", "floor", "blueprint", "blueprint_width", "blueprint_height"]
        labels = {
            "name": "Tên phòng",
            "room_type": "Loại phòng",
            "capacity": "Sức chứa",
            "floor": "Tầng",
            "blueprint": "Sơ đồ phòng (hình ảnh)",
            "blueprint_width": "Chiều rộng sơ đồ (px, tùy chọn)",
            "blueprint_height": "Chiều cao sơ đồ (px, tùy chọn)",
        }
        widgets = {
            "blueprint": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        self.fields["building"].queryset = Building.objects.select_related("university_branch").order_by("name")
        self.fields["floor"].queryset = Floor.objects.select_related("building").order_by("building__name", "level", "name")
        self.fields["floor"].label_from_instance = lambda obj: f"{obj.name} - {obj.building.name if obj.building else '-'}"
        if self.instance and self.instance.pk and self.instance.floor:
            fb = self.instance.floor.building
            if fb:
                self.fields["building"].initial = fb
                if fb.university_branch_id:
                    self.fields["university_branch"].initial = fb.university_branch
        posted_branch = self.data.get("university_branch")
        posted_building = self.data.get("building")
        fq = self.fields["floor"].queryset
        if posted_branch:
            fq = fq.filter(building__university_branch_id=posted_branch)
        if posted_building:
            fq = fq.filter(building_id=posted_building)
        self.fields["floor"].queryset = fq
        if self.instance and self.instance.pk and self.instance.geom:
            centroid = self.instance.geom.centroid
            self.fields["latitude"].initial = centroid.y
            self.fields["longitude"].initial = centroid.x
            self.fields["geom_wkt"].initial = self.instance.geom.wkt

    def clean(self):
        cleaned = super().clean()
        capacity = cleaned.get("capacity")
        if capacity is not None and capacity < 0:
            self.add_error("capacity", "Sức chứa không được âm.")
        floor = cleaned.get("floor")
        building = cleaned.get("building")
        branch = cleaned.get("university_branch")
        if floor:
            if building and floor.building_id != building.id:
                self.add_error("floor", "Tầng không thuộc tòa nhà đã chọn.")
            if branch and (not floor.building or floor.building.university_branch_id != branch.id):
                self.add_error("floor", "Tầng không thuộc chi nhánh đã chọn.")
        name = (cleaned.get("name") or "").strip()
        if floor and name:
            qs = Room.objects.filter(floor=floor, name=name)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("name", "Tên phòng đã tồn tại trong cùng tầng. Vui lòng nhập tên khác.")
        geom_wkt = (cleaned.get("geom_wkt") or "").strip()
        if geom_wkt:
            try:
                geom = GEOSGeometry(geom_wkt, srid=4326)
            except Exception:
                self.add_error("geom_wkt", "Dữ liệu polygon không hợp lệ. Vui lòng vẽ lại trên bản đồ.")
            else:
                if geom.geom_type != "Polygon":
                    self.add_error("geom_wkt", "Hình dạng phòng phải là Polygon.")
                else:
                    try:
                        _validate_polygon_vertices_non_negative(geom)
                    except forms.ValidationError as e:
                        self.add_error("geom_wkt", e.messages[0] if e.messages else str(e))
                    else:
                        cleaned["geom"] = geom
                        centroid = geom.centroid
                        cleaned["latitude"] = centroid.y
                        cleaned["longitude"] = centroid.x
        else:
            cleaned["geom"] = self.instance.geom if self.instance and self.instance.pk else None
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if "geom" in self.cleaned_data:
            obj.geom = self.cleaned_data["geom"]
        if commit:
            obj.save()
        return obj

# ----- Thêm mới: FloorAdminForm -----
class FloorAdminForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ["name", "level", "building"]
        labels = {
            "name": "Tên tầng",
            "level": "Cấp độ (Số tầng)",
            "building": "Tòa nhà",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "VD: Tầng 1, Tầng Trệt"}),
            "level": forms.NumberInput(attrs={"placeholder": "VD: 1, 2, 3..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)

    def clean_level(self):
        level = self.cleaned_data.get("level")
        if level is not None and level < 0:
            raise forms.ValidationError("Tầng không được âm.")
        return level

    def clean(self):
        cleaned = super().clean()
        building = cleaned.get("building")
        name = (cleaned.get("name") or "").strip()
        level = cleaned.get("level")
        if building and name:
            qs = Floor.objects.filter(building=building, name=name)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("name", "Tên tầng đã tồn tại trong cùng tòa nhà.")
        if building and level is not None:
            qs = Floor.objects.filter(building=building, level=level)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("level", "Level tầng đã tồn tại trong cùng tòa nhà.")
        return cleaned


# ----- Building (Polygon - WKT) -----
class BuildingAdminForm(forms.ModelForm):
    geom_wkt = forms.CharField(
        required=False,
        label="Hình dạng (WKT Polygon)",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "POLYGON((106.665 10.798, 106.666 10.798, 106.666 10.799, 106.665 10.799, 106.665 10.798))"})
    )

    class Meta:
        model = Building
        fields = ["name", "description", "university_branch"]
        labels = {
            "name": "Tên tòa nhà",
            "description": "Mô tả",
            "university_branch": "Chi nhánh",
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
            _validate_polygon_vertices_non_negative(geom)
            return geom
        except forms.ValidationError:
            raise
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
    latitude = forms.FloatField(
        required=False,
        label="Vĩ độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0"}),
    )
    longitude = forms.FloatField(
        required=False,
        label="Kinh độ",
        widget=forms.NumberInput(attrs={"step": "0.000001", "min": "0"}),
    )

    class Meta:
        model = Incident
        fields = ["title", "description", "reported_at", "status", "priority", "asset", "building", "floor", "room", "incident_type"]
        labels = {
            "title": "Tiêu đề",
            "description": "Mô tả",
            "reported_at": "Thời gian sự cố",
            "status": "Trạng thái",
            "priority": "Mức độ ưu tiên",
            "asset": "Tài sản",
            "building": "Tòa nhà",
            "floor": "Tầng",
            "room": "Phòng",
            "incident_type": "Loại sự cố",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Tiêu đề sự cố"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "reported_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        self.fields["reported_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
        if self.instance and self.instance.pk and self.instance.reported_at:
            self.initial["reported_at"] = self.instance.reported_at.strftime("%Y-%m-%dT%H:%M")
        self.fields["asset"].queryset = Asset.objects.select_related(
            "equipment", "equipment__room", "equipment__room__floor", "equipment__room__floor__building",
            "tree", "tree__university_branch"
        ).order_by("id")
        self.fields["asset"].label_from_instance = lambda obj: str(obj)
        self.fields["building"].queryset = Building.objects.select_related("university_branch").order_by("name")
        self.fields["floor"].queryset = Floor.objects.select_related("building").order_by("building__name", "level", "name")
        self.fields["room"].queryset = Room.objects.select_related("floor", "floor__building").order_by("name")
        self.fields["floor"].label_from_instance = lambda obj: f"{obj.name} - {obj.building.name if obj.building else '-'}"
        self.fields["room"].label_from_instance = lambda obj: (
            f"{obj.name} - {obj.floor.name if obj.floor else '-'} - "
            f"{obj.floor.building.name if obj.floor and obj.floor.building else '-'}"
        )
        # Always keep full queryset to avoid "selected choice is invalid"
        # when UI dynamically switches contexts before submit.
        self.fields["incident_type"].queryset = IncidentType.objects.all().order_by("name")
        if self.instance and self.instance.pk and self.instance.geom:
            self.fields["latitude"].initial = self.instance.geom.y
            self.fields["longitude"].initial = self.instance.geom.x
        if self.instance and self.instance.pk and self.instance.asset_id:
            atype = Asset.objects.filter(pk=self.instance.asset_id).values_list("asset_type", flat=True).first()
            if atype == "tree":
                self.initial["building"] = None
                self.initial["floor"] = None
                self.initial["room"] = None

    def _filter_incident_type_queryset(self):
        asset = self.data.get("asset") or (self.initial.get("asset") if hasattr(self, "initial") else None)
        building = self.data.get("building") or (self.initial.get("building") if hasattr(self, "initial") else None)
        floor = self.data.get("floor") or (self.initial.get("floor") if hasattr(self, "initial") else None)
        room = self.data.get("room") or (self.initial.get("room") if hasattr(self, "initial") else None)
        if not asset and self.instance and self.instance.pk:
            asset = self.instance.asset_id
        if not building and self.instance and self.instance.pk:
            building = self.instance.building_id
        if not floor and self.instance and self.instance.pk:
            floor = self.instance.floor_id
        if not room and self.instance and self.instance.pk:
            room = self.instance.room_id
        asset_obj = None
        if asset:
            try:
                asset_obj = Asset.objects.filter(pk=asset).first()
            except Exception:
                asset_obj = None
        contexts = set()
        if asset_obj and asset_obj.asset_type in ("equipment", "tree"):
            contexts.add(asset_obj.asset_type)
            contexts.add("security")
        if not asset_obj and (building or floor or room):
            contexts.add("emergency")
        elif building or floor or room:
            contexts.add("facility")

        if contexts:
            type_ids = []
            for it in IncidentType.objects.all():
                if set(it.applies_to or []).intersection(contexts):
                    type_ids.append(it.id)
            self.fields["incident_type"].queryset = IncidentType.objects.filter(id__in=type_ids).order_by("name")
        else:
            self.fields["incident_type"].queryset = IncidentType.objects.all().order_by("name")

    def clean(self):
        cleaned = super().clean()
        asset = cleaned.get("asset")
        building = cleaned.get("building")
        floor = cleaned.get("floor")
        room = cleaned.get("room")
        incident_type = cleaned.get("incident_type")

        if asset and asset.asset_type == "tree":
            cleaned["building"] = None
            cleaned["floor"] = None
            cleaned["room"] = None
            building = floor = room = None

        # Auto-fill location from selected equipment asset if user left location empty.
        if asset and asset.asset_type == "equipment" and asset.equipment and asset.equipment.room:
            eq_room = asset.equipment.room
            eq_floor = eq_room.floor
            eq_building = eq_floor.building if eq_floor else None
            if room is None:
                cleaned["room"] = eq_room
                room = eq_room
            if floor is None and eq_floor is not None:
                cleaned["floor"] = eq_floor
                floor = eq_floor
            if building is None and eq_building is not None:
                cleaned["building"] = eq_building
                building = eq_building

        contexts = set()
        if asset and asset.asset_type in ("equipment", "tree"):
            contexts.add(asset.asset_type)
            contexts.add("security")
        if not asset and (building or floor or room):
            contexts.add("emergency")
        elif building or floor or room:
            contexts.add("facility")
        if contexts:
            # Auto pick emergency type when only location is selected and incident_type left empty.
            if not incident_type and "emergency" in contexts:
                incident_type = IncidentType.objects.filter(applies_to__contains=["emergency"]).order_by("id").first()
                if incident_type:
                    cleaned["incident_type"] = incident_type
            if incident_type and not set(incident_type.applies_to or []).intersection(contexts):
                self.add_error("incident_type", "Loại sự cố không phù hợp với tài sản/vị trí đã chọn.")

        if room and floor and room.floor_id != floor.id:
            self.add_error("room", "Phòng không thuộc tầng đã chọn.")
        if floor and building and floor.building_id != building.id:
            self.add_error("floor", "Tầng không thuộc tòa nhà đã chọn.")
        if room and building and room.floor and room.floor.building_id != building.id:
            self.add_error("room", "Phòng không thuộc tòa nhà đã chọn.")

        # If user only selected location without asset, force emergency group.
        if not asset and (building or floor or room) and incident_type:
            applies = set(incident_type.applies_to or [])
            if "emergency" not in applies:
                self.add_error("incident_type", "Khi chỉ chọn vị trí (tòa/tầng/phòng) mà không chọn tài sản, loại sự cố phải thuộc Khẩn cấp.")

        if asset and asset.asset_type == "tree" and asset.tree and asset.tree.geom:
            lat_raw, lng_raw = cleaned.get("latitude"), cleaned.get("longitude")
            if lat_raw in (None, "") or lng_raw in (None, ""):
                cleaned["latitude"] = float(asset.tree.geom.y)
                cleaned["longitude"] = float(asset.tree.geom.x)

        lat, lng = cleaned.get("latitude"), cleaned.get("longitude")
        if lat is None or lng is None:
            self.add_error("latitude", "Vui lòng chọn vị trí trên bản đồ hoặc nhập tọa độ.")
            return cleaned
        coord_bad = False
        if lat < 0:
            self.add_error("latitude", "Vĩ độ không được âm.")
            coord_bad = True
        if lng < 0:
            self.add_error("longitude", "Kinh độ không được âm.")
            coord_bad = True
        if coord_bad:
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
        fields = ["code", "name", "applies_to", "description", "default_severity"]
        labels = {
            "code": "Mã loại sự cố",
            "name": "Tên loại sự cố",
            "applies_to": "Áp dụng cho",
            "description": "Mô tả",
            "default_severity": "Mức độ nghiêm trọng mặc định (1-5)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        self.fields["applies_to"] = forms.MultipleChoiceField(
            choices=IncidentType.APPLIES_TO_CHOICES,
            required=True,
            label="Áp dụng cho",
            widget=forms.CheckboxSelectMultiple(),
        )
        initial_applies = self.initial.get("applies_to")
        if isinstance(initial_applies, list):
            self.fields["applies_to"].initial = initial_applies
        elif self.instance and self.instance.pk:
            self.fields["applies_to"].initial = self.instance.applies_to

    def clean(self):
        cleaned = super().clean()
        applies_to = cleaned.get("applies_to") or []
        if "emergency" in applies_to:
            cleaned["default_severity"] = 5
        return cleaned


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
        # Chỉ hiện thiết bị / cây chưa gắn tài sản khác (trừ bản ghi đang sửa) — tránh trùng, dễ quản lý.
        used_equipment = Asset.objects.filter(equipment__isnull=False)
        used_tree = Asset.objects.filter(tree__isnull=False)
        if self.instance.pk:
            used_equipment = used_equipment.exclude(pk=self.instance.pk)
            used_tree = used_tree.exclude(pk=self.instance.pk)
        used_eq_ids = list(used_equipment.values_list("equipment_id", flat=True))
        used_tree_ids = list(used_tree.values_list("tree_id", flat=True))

        self.fields["equipment"].queryset = Equipment.objects.select_related(
            "room", "room__floor", "room__floor__building", "room__floor__building__university_branch"
        ).exclude(pk__in=used_eq_ids).order_by("code")
        self.fields["equipment"].label_from_instance = lambda obj: (
            f"{obj.code} - {obj.name or '-'} - "
            f"{obj.room.floor.building.university_branch.name if obj.room and obj.room.floor and obj.room.floor.building and obj.room.floor.building.university_branch else '-'} / "
            f"{obj.room.floor.building.name if obj.room and obj.room.floor and obj.room.floor.building else '-'} / "
            f"{obj.room.floor.name if obj.room and obj.room.floor else '-'} / "
            f"{obj.room.name if obj.room else '-'}"
        )
        self.fields["tree"].queryset = (
            Tree.objects.select_related("university_branch").exclude(pk__in=used_tree_ids).order_by("code")
        )
        self.fields["tree"].label_from_instance = lambda obj: f"{obj.code} - {obj.species or '-'} - {obj.university_branch.name if obj.university_branch else '-'}"

    def clean(self):
        cleaned = super().clean()
        asset_type = cleaned.get("asset_type")
        equipment = cleaned.get("equipment")
        tree = cleaned.get("tree")
        if asset_type == "equipment" and not equipment:
            self.add_error("equipment", "Vui lòng chọn thiết bị.")
        if asset_type == "tree" and not tree:
            self.add_error("tree", "Vui lòng chọn cây.")
        return cleaned


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
        self.fields["asset"].queryset = Asset.objects.select_related(
            "equipment", "tree"
        ).order_by("id")
        self.fields["asset"].label_from_instance = lambda obj: str(obj)

        # Nhân viên phụ trách chỉ lấy các tài khoản có role thuộc nhóm CSVC.
        # Đồng thời hiển thị nhãn dạng: username (role) để phân biệt rõ trên dropdown.
        technical_role_names = {
            "ky thuat",
            "nhan vien ky thuat",
            "ky thuat vien",
            "technical",
            "technician",
            "maintenance technician",
        }
        facility_role_names = {
            "facility staff",
            "nhan vien csvc",
            "nhan vien co so vat chat",
            "csvc",
            "co so vat chat",
        }

        def normalize_role_name(name: str) -> str:
            if not name:
                return ""
            normalized = (
                unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode("ascii")
            )
            normalized = normalized.strip().lower().replace("_", " ")
            return " ".join(normalized.split())

        staff_candidates = AppUser.objects.select_related("role").all()
        facility_staff_ids = []
        for u in staff_candidates:
            role_name = u.role.name if u.role else ""
            normalized_role = normalize_role_name(role_name)
            if normalized_role in technical_role_names or normalized_role in facility_role_names:
                facility_staff_ids.append(u.id)

        self.fields["staff"].queryset = (
            AppUser.objects.select_related("role")
            .filter(id__in=facility_staff_ids)
            .order_by("id")
        )
        self.fields["staff"].label_from_instance = (
            lambda obj: f"{obj.username} ({obj.role.name if obj.role else ''})".strip(" ()")
        )

    def clean_cost(self):
        cost = self.cleaned_data.get("cost")
        if cost is not None and cost < 0:
            raise forms.ValidationError("Chi phí không được âm.")
        return cost


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
    if getattr(app_user, "email", ""):
        user.email = app_user.email
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
        fields = ["email", "username", "university_branch", "role"]
        labels = {
            "email": "Email",
            "username": "Tên đăng nhập",
            "university_branch": "Chi nhánh",
            "role": "Vai trò",
        }
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "ten@hcmunre.edu.vn"}),
            "username": forms.TextInput(attrs={"placeholder": "Tên đăng nhập"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
        self.fields["password_plain"].widget.attrs.setdefault("class", "form-control")
        if not self.instance.pk:
            self.fields["password_plain"].required = True
            self.fields["password_plain"].label = "Mật khẩu"

    def clean_email(self):
        return validate_app_user_email_domain(self.cleaned_data.get("email"))

    def save(self, commit=True):
        obj = super().save(commit=False)
        pwd = self.cleaned_data.get("password_plain")
        if pwd:
            from django.contrib.auth.hashers import make_password
            obj.password = make_password(pwd)
        if not self.instance.pk:
            obj.must_change_password = True
        if commit:
            obj.save()
            _sync_appuser_to_django_user(obj)
        return obj


class AboutAnnouncementAdminForm(forms.ModelForm):
    class Meta:
        model = AboutAnnouncement
        fields = ["title", "summary", "content", "thumbnail", "is_published"]
        labels = {
            "title": "Tiêu đề",
            "summary": "Mô tả ngắn",
            "content": "Nội dung chi tiết",
            "thumbnail": "Ảnh thu nhỏ",
            "is_published": "Hiển thị công khai",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "VD: Thông báo tuyển sinh đợt mới"}),
            "summary": forms.Textarea(attrs={"rows": 3, "placeholder": "Mô tả ngắn hiển thị ở danh sách..." }),
            "content": forms.Textarea(attrs={"rows": 8, "placeholder": "Nhập nội dung chi tiết..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)


class AboutHeroSectionAdminForm(forms.ModelForm):
    class Meta:
        model = AboutHeroSection
        fields = ["title", "welcome_text", "background_image", "is_active"]
        labels = {
            "title": "Tiêu đề chính",
            "welcome_text": "Lời ngỏ",
            "background_image": "Ảnh nền Hero",
            "is_active": "Đang sử dụng",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "VD: Hệ thống Quản lý Cơ sở hạ tầng Đại học"}),
            "welcome_text": forms.Textarea(attrs={"rows": 5, "placeholder": "Nhập đoạn mô tả ngắn cho khối Banner & Lời ngỏ..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)


class AboutCoreValueAdminForm(forms.ModelForm):
    class Meta:
        model = AboutCoreValue
        fields = ["title", "description", "image", "display_order", "is_active"]
        labels = {
            "title": "Tên cột",
            "description": "Nội dung",
            "image": "Ảnh minh họa",
            "display_order": "Thứ tự hiển thị",
            "is_active": "Đang hiển thị",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "VD: Phòng Lab nghiên cứu"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Mô tả ngắn cho cột nội dung..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image and not (self.instance and self.instance.pk and self.instance.image):
            raise forms.ValidationError("Vui lòng tải ảnh minh họa. Mục Hiện đại & Công nghệ không còn dùng icon.")
        return image

    def clean_display_order(self):
        display_order = self.cleaned_data.get("display_order")
        if display_order is None:
            return display_order
        qs = AboutCoreValue.objects.filter(display_order=display_order)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Thứ tự hiển thị đã tồn tại. Vui lòng chọn số khác.")
        return display_order


class AboutFeaturedEventAdminForm(forms.ModelForm):
    class Meta:
        model = AboutFeaturedEvent
        fields = ["title", "summary", "image", "event_date", "is_published"]
        labels = {
            "title": "Tiêu đề sự kiện",
            "summary": "Mô tả ngắn",
            "image": "Ảnh sự kiện",
            "event_date": "Ngày sự kiện",
            "is_published": "Đang hiển thị",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "VD: VLU Job Fair 2026"}),
            "summary": forms.Textarea(attrs={"rows": 4, "placeholder": "Mô tả ngắn cho thẻ sự kiện..."}),
            "event_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap(self)
