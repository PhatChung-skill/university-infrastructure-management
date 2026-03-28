from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse

from django.core.serializers import serialize
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from .forms import (
    BootstrapAuthenticationForm,
    FacilityMaintenanceForm,
    FacilityIncidentForm,
)
from .models import (
    Building,
    Tree,
    Incident,
    Equipment,
    AppUser,
    Asset,
    Maintenance,
    Room,
)
import json
import unicodedata
from typing import Optional


def _normalize_role_name(name: Optional[str]) -> str:
    if not name:
        return ""
    normalized = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode("ascii")
    return normalized.strip().lower()


def _current_role_name(request):
    app_user = AppUser.objects.select_related("role").filter(username=request.user.username).first()
    return app_user, _normalize_role_name(app_user.role.name if app_user and app_user.role else "")


def _is_admin_role(role_name: str) -> bool:
    return role_name in {"admin", "quan tri", "quan tri vien", "administrator"}


def _is_facility_role(role_name: str) -> bool:
    return role_name in {
        "facility_staff",
        "nhan vien csvc",
        "nhan vien co so vat chat",
        "csvc",
        "co so vat chat",
    }


def _is_teacher_role(role_name: str) -> bool:
    return role_name in {"teacher", "giang vien", "giao vien"}


class Login(LoginView):
    template_name = 'login.html'
    authentication_form = BootstrapAuthenticationForm

    def get_success_url(self):
        """
        Sau khi đăng nhập:
        - Nếu là tài khoản admin (superuser/staff của Django) HOẶC user thuộc role 'Admin'
          trong bảng AppUser/Role => chuyển sang trang Django Admin (dashboard)
        - Nếu role là 'facility_staff' => chuyển sang trang dashboard nhân viên CSVC
        - Nếu role là 'teacher' => chuyển sang dashboard giảng viên
        - Ngược lại => chuyển sang trang bản đồ (map)
        """
        user = self.request.user
        _, role_name = _current_role_name(self.request)

        # 1. Ưu tiên tài khoản admin của Django (superuser / staff) → custom admin
        if user.is_superuser or user.is_staff:
            return reverse("admin_dashboard")

        # 2. Hoặc người dùng có role trong bảng AppUser/Role
        if role_name:
            if _is_admin_role(role_name):
                return reverse("admin_dashboard")
            # Nhân viên CSVC: chấp nhận cả tên role tiếng Anh và tiếng Việt
            if _is_facility_role(role_name):
                return reverse("facility_dashboard")
            # Giáo viên: chấp nhận cả 'teacher' và 'giảng viên'
            if _is_teacher_role(role_name):
                return reverse("teacher_dashboard")

        return reverse("map_view")


def map_view(request):
    # 1. Lấy dữ liệu và chuyển sang GeoJSON
    # Chúng ta lấy các trường cần thiết để hiển thị Popup (name, description, status...)
    
    buildings_geojson = serialize('geojson', Building.objects.all(), 
                                  geometry_field='geom', 
                                  fields=('name', 'description'))
    
    trees_geojson = serialize('geojson', Tree.objects.all(), 
                              geometry_field='geom', 
                              fields=('code', 'species', 'health_status'))
    
    # Incidents: tự build GeoJSON để thêm thông tin loại sự cố, loại tài sản, tên tài sản
    VI_PRIORITY = {"low": "Thấp", "medium": "Trung bình", "high": "Cao"}
    VI_STATUS = {"open": "Mở", "processing": "Đang xử lý", "closed": "Đã đóng"}
    incidents_features = []
    for inc in Incident.objects.select_related("incident_type", "asset", "asset__equipment", "asset__tree").all():
        if not inc.geom:
            continue
        geom = json.loads(inc.geom.geojson)
        asset = inc.asset
        asset_search = []
        if asset:
            if asset.asset_type == "equipment" and asset.equipment:
                e = asset.equipment
                asset_search = [e.name or "", e.code or "", e.equipment_type or ""]
                blueprint_url = ""
                if getattr(e, "room", None) and getattr(e.room, "blueprint_url", None):
                    blueprint_url = e.room.blueprint_url
            elif asset.asset_type == "tree" and asset.tree:
                t = asset.tree
                asset_search = [t.species or "", t.code or ""]
                blueprint_url = ""
            else:
                blueprint_url = ""
        else:
            blueprint_url = ""
        asset_search_text = " ".join(s.strip() for s in asset_search if s).strip()
        props = {
            "title": inc.title,
            "status": inc.status,
            "priority": inc.priority,
            "vi_priority": VI_PRIORITY.get(inc.priority, inc.priority),
            "vi_status": VI_STATUS.get(inc.status, inc.status),
            "incident_type": inc.incident_type.name if inc.incident_type else "",
            "incident_type_code": inc.incident_type.code if inc.incident_type else "",
            "asset_type": asset.asset_type if asset else "",
            "asset_search_text": asset_search_text,
            "image_url": blueprint_url,
        }
        incidents_features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": props,
            }
        )
    incidents_geojson = json.dumps(
        {"type": "FeatureCollection", "features": incidents_features}
    )

    # Rooms: tự build GeoJSON để bổ sung thông tin tầng/tòa nhà + ảnh blueprint
    room_features = []
    for room in Room.objects.select_related("floor", "floor__building").exclude(geom__isnull=True):
        room_features.append(
            {
                "type": "Feature",
                "geometry": json.loads(room.geom.geojson),
                "properties": {
                    "id": room.id,
                    "name": room.name,
                    "room_type": room.room_type,
                    "capacity": room.capacity,
                    "floor_name": room.floor.name if room.floor else "",
                    "building_name": room.floor.building.name if room.floor and room.floor.building else "",
                    "blueprint_url": room.blueprint_url or "",
                    "blueprint_width": room.blueprint_width,
                    "blueprint_height": room.blueprint_height,
                },
            }
        )
    rooms_geojson = json.dumps({"type": "FeatureCollection", "features": room_features})

    # Equipment: bổ sung phòng/tầng/tòa nhà + ảnh blueprint của phòng
    equipment_features = []
    for eq in (
        Equipment.objects.exclude(geom__isnull=True)
        .select_related("room", "room__floor", "room__floor__building")
    ):
        equipment_features.append(
            {
                "type": "Feature",
                "geometry": json.loads(eq.geom.geojson),
                "properties": {
                    "id": eq.id,
                    "code": eq.code,
                    "name": eq.name,
                    "status": eq.status,
                    "equipment_type": eq.equipment_type,
                    "room_name": eq.room.name if eq.room else "",
                    "floor_name": eq.room.floor.name if eq.room and eq.room.floor else "",
                    "building_name": eq.room.floor.building.name if eq.room and eq.room.floor and eq.room.floor.building else "",
                    "blueprint_url": (eq.room.blueprint_url if eq.room else "") or "",
                },
            }
        )
    equipment_geojson = json.dumps({"type": "FeatureCollection", "features": equipment_features})

    # 2. Xác định nút quay lại phù hợp (Admin hoặc Nhân viên CSVC)
    back_url = None
    back_label = None

    if request.user.is_authenticated:
        _, role_name = _current_role_name(request)

        # Admin (custom admin dashboard)
        if request.user.is_superuser or request.user.is_staff or _is_admin_role(role_name):
            back_url = reverse("admin_dashboard")
            back_label = "← Quay lại trang quản trị"
        # Nhân viên CSVC (cả tiếng Anh & tiếng Việt)
        elif _is_facility_role(role_name):
            back_url = reverse("facility_dashboard")
            back_label = "← Quay lại dashboard CSVC"
        # Giáo viên
        elif _is_teacher_role(role_name):
            back_url = reverse("teacher_dashboard")
            back_label = "← Quay lại dashboard GV"

    # 3. Truyền dữ liệu sang template
    context = {
        'buildings_json': buildings_geojson,
        'trees_json': trees_geojson,
        'incidents_json': incidents_geojson,
        'rooms_json': rooms_geojson,
        'equipment_json': equipment_geojson,
        'back_url': back_url,
        'back_label': back_label,
    }
    return render(request, 'home/map.html', context)


@login_required
def radius_search(request):
    """
    Truy vấn bán kính quanh 1 điểm (cây, thiết bị, phòng).
    Nhận tham số: lat, lng, radius (m), layers (vd: trees,devices,rooms).
    Trả về GeoJSON cho từng lớp trong bán kính đó.
    """
    try:
        lat = float(request.GET.get("lat"))
        lng = float(request.GET.get("lng"))
        radius = float(request.GET.get("radius", "20"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Tham số lat/lng/radius không hợp lệ."}, status=400)

    point = Point(lng, lat, srid=4326)
    layers_param = request.GET.get("layers", "trees,devices,rooms")
    layer_names = {name.strip() for name in layers_param.split(",") if name.strip()}

    result = {}

    def to_feature_collection(objs, geom_attr="geom", extra_props=None):
        features = []
        for obj in objs:
            geom = getattr(obj, geom_attr, None)
            if not geom:
                continue
            props = {}
            if isinstance(obj, Tree):
                props = {
                    "id": obj.id,
                    "type": "tree",
                    "code": obj.code,
                    "species": obj.species,
                    "health_status": obj.health_status,
                }
            elif isinstance(obj, Equipment):
                props = {
                    "id": obj.id,
                    "type": "equipment",
                    "code": obj.code,
                    "name": obj.name,
                    "status": obj.status,
                    "equipment_type": obj.equipment_type,
                    "room_name": obj.room.name if getattr(obj, "room", None) else "",
                    "floor_name": obj.room.floor.name if getattr(obj, "room", None) and getattr(obj.room, "floor", None) else "",
                    "building_name": (
                        obj.room.floor.building.name
                        if getattr(obj, "room", None)
                        and getattr(obj.room, "floor", None)
                        and getattr(obj.room.floor, "building", None)
                        else ""
                    ),
                    "blueprint_url": (obj.room.blueprint_url if getattr(obj, "room", None) else "") or "",
                }
            elif isinstance(obj, Room):
                props = {
                    "id": obj.id,
                    "type": "room",
                    "name": obj.name,
                    "room_type": obj.room_type,
                    "capacity": obj.capacity,
                    "floor_name": obj.floor.name if getattr(obj, "floor", None) else "",
                    "building_name": (
                        obj.floor.building.name
                        if getattr(obj, "floor", None) and getattr(obj.floor, "building", None)
                        else ""
                    ),
                    "blueprint_url": obj.blueprint_url or "",
                    "blueprint_width": obj.blueprint_width,
                    "blueprint_height": obj.blueprint_height,
                }
            if extra_props:
                props.update(extra_props(obj))
            features.append(
                {
                    "type": "Feature",
                    "geometry": json.loads(geom.geojson),
                    "properties": props,
                }
            )
        return {"type": "FeatureCollection", "features": features}

    if "trees" in layer_names:
        trees_qs = Tree.objects.filter(geom__distance_lte=(point, D(m=radius)))
        result["trees"] = to_feature_collection(trees_qs)

    if "devices" in layer_names or "equipment" in layer_names:
        equip_qs = (
            Equipment.objects.filter(geom__distance_lte=(point, D(m=radius)))
            .select_related("room", "room__floor", "room__floor__building")
        )
        result["equipment"] = to_feature_collection(equip_qs)

    if "rooms" in layer_names:
        rooms_qs = (
            Room.objects.exclude(geom__isnull=True)
            .filter(geom__distance_lte=(point, D(m=radius)))
            .select_related("floor", "floor__building")
        )
        result["rooms"] = to_feature_collection(rooms_qs)

    return JsonResponse(result)


@login_required
def dangerous_trees_near_rooms(request):
    """
    Truy vấn tất cả cây có health_status='dangerous'.
    Trả về FeatureCollection các cây nguy hiểm.
    """
    dangerous_trees = Tree.objects.filter(health_status="dangerous").exclude(geom__isnull=True)

    features = []
    for tree in dangerous_trees:
        geom = tree.geom
        if not geom:
            continue
        props = {
            "id": tree.id,
            "type": "tree",
            "code": tree.code,
            "species": tree.species,
            "health_status": tree.health_status,
        }
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(geom.geojson),
                "properties": props,
            }
        )

    return JsonResponse({"type": "FeatureCollection", "features": features})


@login_required
def devices_to_check(request):
    """
    Truy vấn các thiết bị cần kiểm tra/bảo trì.
    Ở đây định nghĩa đơn giản: thiết bị có status != 'good'.
    Có thể mở rộng thêm điều kiện theo last_maintenance nếu cần.
    """
    devices_qs = (
        Equipment.objects.exclude(geom__isnull=True)
        .exclude(status="good")
        .select_related("room")
    )

    features = []
    for device in devices_qs:
        geom = device.geom
        if not geom:
            continue
        room = device.room
        props = {
            "id": device.id,
            "type": "equipment",
            "code": device.code,
            "name": device.name,
            "status": device.status,
            "room_name": room.name if room else "",
            "blueprint_url": room.blueprint_url if room else "",
        }
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(geom.geojson),
                "properties": props,
            }
        )

    return JsonResponse({"type": "FeatureCollection", "features": features})


from .decorators import admin_required


@admin_required
def admin_dashboard(request):
    """
    Trang quản trị hệ thống dành cho role 'Admin'.
    Nếu user không phải Admin thì tự động chuyển về trang bản đồ.
    """
    return render(request, "home/admin_dashboard.html")


@login_required
def facility_dashboard(request):
    """
    Dashboard dành cho Nhân viên CSVC (role = 'facility_staff').
    Cho phép tạo phiếu bảo trì tài sản (thiết bị / cây) nhưng KHÔNG cho quản lý user & phân quyền.
    """
    app_user, role_name = _current_role_name(request)

    # Chỉ cho phép role Nhân viên CSVC (tiếng Anh hoặc tiếng Việt)
    if not (app_user and _is_facility_role(role_name)):
        return redirect("map_view")

    if request.method == "POST":
        form = FacilityMaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.staff = app_user
            maintenance.save()
            messages.success(request, "Đã ghi nhận bảo trì tài sản thành công.")
            return redirect("facility_dashboard")
    else:
        form = FacilityMaintenanceForm()

    recent_maintenances = (
        Maintenance.objects.filter(staff=app_user)
        .select_related("asset")
        .order_by("-maintenance_date")[:5]
    )

    context = {
        "form": form,
        "recent_maintenances": recent_maintenances,
    }
    return render(request, "home/facility_dashboard.html", context)


@login_required
def facility_incident(request):
    """
    Trang Báo cáo sự cố dành cho Nhân viên CSVC.
    """
    app_user, role_name = _current_role_name(request)

    if not (app_user and _is_facility_role(role_name)):
        return redirect("map_view")

    if request.method == "POST":
        form = FacilityIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)

            # Thiết lập vị trí sự cố theo vị trí tài sản
            asset = incident.asset
            if asset.asset_type == "equipment" and asset.equipment:
                incident.geom = asset.equipment.geom
            elif asset.asset_type == "tree" and asset.tree:
                incident.geom = asset.tree.geom

            incident.status = "open"
            incident.save()
            messages.success(request, "Đã ghi nhận báo cáo sự cố thành công.")
            return redirect("facility_incident")
    else:
        form = FacilityIncidentForm()

    recent_incidents = (
        Incident.objects.select_related("asset", "incident_type")
        .order_by("-reported_at")[:5]
    )

    context = {
        "form": form,
        "recent_incidents": recent_incidents,
    }
    return render(request, "home/facility_incident.html", context)


def logout_view(request):
    """
    Đăng xuất khỏi hệ thống và luôn quay về trang login.
    Dùng cho nút Đăng xuất trên giao diện Nhân viên CSVC.
    """
    logout(request)
    return redirect("login")


@login_required
def teacher_dashboard(request):
    """
    Dashboard read-only cho Giảng viên:
    - Xem danh sách phòng học và trạng thái (tốt / hỏng / đang sửa) dựa trên thiết bị trong phòng
    - Chuyển sang bản đồ để xem vị trí
    """
    app_user, role_name = _current_role_name(request)

    if not (app_user and _is_teacher_role(role_name)):
        return redirect("map_view")

    # Lấy danh sách phòng + thiết bị để tính trạng thái
    rooms = Room.objects.select_related("floor", "floor__building").prefetch_related("equipment_set").all()

    room_status_list = []
    for room in rooms:
        statuses = {eq.status for eq in room.equipment_set.all()}
        if "broken" in statuses:
            status_label = "Hỏng"
            status_badge = "danger"
        elif "maintenance" in statuses:
            status_label = "Đang sửa"
            status_badge = "warning"
        elif statuses:
            status_label = "Hoạt động tốt"
            status_badge = "success"
        else:
            status_label = "Chưa có thiết bị"
            status_badge = "secondary"

        room_status_list.append(
            {
                "room": room,
                "status_label": status_label,
                "status_badge": status_badge,
            }
        )

    context = {
        "room_status_list": room_status_list,
    }
    return render(request, "home/teacher_dashboard.html", context)