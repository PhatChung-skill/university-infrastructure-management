from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from django.contrib import messages

from .forms import (
    BootstrapAuthenticationForm,
    FacilityMaintenanceForm,
    FacilityIncidentForm,
)
from django.core.serializers import serialize
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
        app_user = AppUser.objects.select_related("role").filter(username=user.username).first()

        # 1. Ưu tiên tài khoản admin của Django (superuser / staff)
        if user.is_superuser or user.is_staff:
            return reverse("admin:index")

        # 2. Hoặc người dùng có role trong bảng AppUser/Role
        if app_user and app_user.role:
            role_name = app_user.role.name.lower()
            if role_name == "admin":
                return reverse("admin:index")
            # Nhân viên CSVC: chấp nhận cả tên role tiếng Anh và tiếng Việt
            if role_name in ("facility_staff", "nhân viên csvc"):
                return reverse("facility_dashboard")
            # Giáo viên: chấp nhận cả 'teacher' và 'giảng viên'
            if role_name in ("teacher", "giảng viên"):
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
    
    incidents_geojson = serialize('geojson', Incident.objects.all(),
                                  geometry_field='geom',
                                  fields=('title', 'status', 'priority'))

    # 2. Xác định nút quay lại phù hợp (Admin hoặc Nhân viên CSVC)
    back_url = None
    back_label = None

    if request.user.is_authenticated:
        app_user = AppUser.objects.select_related("role").filter(
            username=request.user.username
        ).first()

        role_name = app_user.role.name.lower() if app_user and app_user.role else None

        # Admin Django hoặc role Admin
        if request.user.is_superuser or request.user.is_staff or role_name == "admin":
            back_url = reverse("admin:index")
            back_label = "← Quay lại trang admin"
        # Nhân viên CSVC (cả tiếng Anh & tiếng Việt)
        elif role_name in ("facility_staff", "nhân viên csvc"):
            back_url = reverse("facility_dashboard")
            back_label = "← Quay lại dashboard CSVC"
        # Giáo viên
        elif role_name in ("teacher", "giảng viên"):
            back_url = reverse("teacher_dashboard")
            back_label = "← Quay lại dashboard GV"

    # 3. Truyền dữ liệu sang template
    context = {
        'buildings_json': buildings_geojson,
        'trees_json': trees_geojson,
        'incidents_json': incidents_geojson,
        'back_url': back_url,
        'back_label': back_label,
    }
    return render(request, 'home/map.html', context)


@login_required
def admin_dashboard(request):
    """
    Trang quản trị hệ thống dành cho role 'Admin'.
    Nếu user không phải Admin thì tự động chuyển về trang bản đồ.
    """
    app_user = AppUser.objects.select_related("role").filter(username=request.user.username).first()

    if not (app_user and app_user.role and app_user.role.name.lower() == "admin"):
        return redirect("map_view")

    return render(request, "home/admin_dashboard.html")


@login_required
def facility_dashboard(request):
    """
    Dashboard dành cho Nhân viên CSVC (role = 'facility_staff').
    Cho phép tạo phiếu bảo trì tài sản (thiết bị / cây) nhưng KHÔNG cho quản lý user & phân quyền.
    """
    app_user = AppUser.objects.select_related("role").filter(username=request.user.username).first()

    # Chỉ cho phép role Nhân viên CSVC (tiếng Anh hoặc tiếng Việt)
    if not (
        app_user
        and app_user.role
        and app_user.role.name.lower() in ("facility_staff", "nhân viên csvc")
    ):
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
    app_user = AppUser.objects.select_related("role").filter(username=request.user.username).first()

    if not (
        app_user
        and app_user.role
        and app_user.role.name.lower() in ("facility_staff", "nhân viên csvc")
    ):
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
    app_user = AppUser.objects.select_related("role").filter(username=request.user.username).first()

    if not (
        app_user
        and app_user.role
        and app_user.role.name.lower() in ("teacher", "giảng viên")
    ):
        return redirect("map_view")

    # Lấy danh sách phòng + thiết bị để tính trạng thái
    rooms = (
        Room.objects.select_related("building")
        .prefetch_related("equipment_set")
        .all()
    )

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