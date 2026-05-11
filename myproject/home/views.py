from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.core.serializers import serialize
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.utils import OperationalError, ProgrammingError

from .forms import (
    BootstrapAuthenticationForm,
    ForgotPasswordEmailForm,
    VerifySixDigitForm,
    BootstrapSetPasswordForm,
    BootstrapPasswordChangeForm,
    FacilityMaintenanceForm,
    FacilityIncidentForm,
    TeacherQuickIncidentReportForm,
)
from .models import (
    UniversityBranch,
    Building,
    Floor,
    Tree,
    Incident,
    Equipment,
    AppUser,
    Asset,
    Maintenance,
    Room,
    QuickIncidentReport,
    IncidentType,
    PasswordResetCode,
    AboutHeroSection,
    AboutCoreValue,
    AboutAnnouncement,
    AboutFeaturedEvent,
)
from .password_reset_utils import (
    generate_six_digit_code,
    hash_reset_code,
    send_password_reset_code_email,
)
from .map_utils import (
    buildings_geojson_dumps,
    floor_equipment_map_payload,
    floor_rooms_geojson,
    floors_payload_for_building,
    room_blueprint_display_url,
    room_layout_payload,
)
import json
import unicodedata
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

# Số dòng cố định mỗi trang trên dashboard giảng viên (bảng phòng + dòng trống pad).
TEACHER_ROOMS_PER_PAGE = 10
# Tìm phòng trên trang chủ — số kết quả mỗi trang (phân trang + fetch, không reload).
HOME_ROOM_SEARCH_PER_PAGE = 10


def _teacher_room_status_search_blob(item: dict) -> str:
    """Chuỗi tìm kiếm thô: tòa, tầng, phòng, loại phòng, tình trạng (VN + mã), thiết bị."""
    room = item["room"]
    fl = room.floor
    bld = fl.building if fl else None
    parts = [
        room.name or "",
        (fl.name if fl else "") or "",
        (bld.name if bld else "") or "",
        room.get_room_type_display() or "",
        (room.room_type or ""),
        item.get("status_label") or "",
    ]
    for eq in room.equipment_set.all():
        parts.extend(
            [
                eq.code or "",
                eq.name or "",
                eq.equipment_type or "",
                eq.status or "",
            ]
        )
    return " ".join(parts).lower()


def _teacher_room_status_matches(item: dict, query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return True
    blob = _teacher_room_status_search_blob(item)
    for token in q.split():
        t = token.strip()
        if t and t not in blob:
            return False
    return True


def _normalize_role_name(name: Optional[str]) -> str:
    if not name:
        return ""
    normalized = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.strip().lower().replace("_", " ")
    return " ".join(normalized.split())


def _current_role_name(request):
    app_user = AppUser.objects.select_related("role").filter(username=request.user.username).first()
    return app_user, _normalize_role_name(app_user.role.name if app_user and app_user.role else "")


def _is_admin_role(role_name: str) -> bool:
    return role_name in {"admin", "quan tri", "quan tri vien", "administrator"}


def _is_facility_role(role_name: str) -> bool:
    return role_name in {
        "facility staff",
        "nhan vien csvc",
        "nhan vien co so vat chat",
        "csvc",
        "co so vat chat",
    }


def _is_technical_staff_role(role_name: str) -> bool:
    """Nhân viên kỹ thuật / bảo trì — cùng khu chức năng phiếu bảo trì & báo cáo sự cố với CSVC."""
    return role_name in {
        "ky thuat",
        "nhan vien ky thuat",
        "ky thuat vien",
        "technical",
        "technician",
        "maintenance technician",
    }


def _is_facility_or_technical_staff(role_name: str) -> bool:
    return _is_facility_role(role_name) or _is_technical_staff_role(role_name)


def _is_teacher_role(role_name: str) -> bool:
    return role_name in {"teacher", "giang vien", "giao vien", "lecturer"}


def _requires_password_change(app_user, role_name: str) -> bool:
    return bool(
        app_user
        and app_user.must_change_password
        and (_is_facility_or_technical_staff(role_name) or _is_teacher_role(role_name))
    )


def home(request):
    """
    Trang chủ (landing page) hiển thị trước đăng nhập và vẫn truy cập được sau đăng nhập.
    """
    branches_count = UniversityBranch.objects.count()
    buildings_count = Building.objects.count()
    rooms_count = Room.objects.count()
    equipment_count = Equipment.objects.count()
    trees_count = Tree.objects.count()

    app_user = None
    role_name = ""
    if request.user.is_authenticated:
        app_user, role_name = _current_role_name(request)

    # --- Tìm kiếm phòng học (GET ?q= & room_id=) ---
    q_raw = (request.GET.get("q") or "").strip()
    room_id_raw = request.GET.get("room_id")
    searched_room = None
    room_search_page = None
    if room_id_raw:
        try:
            rid = int(room_id_raw)
            searched_room = (
                Room.objects.select_related("floor", "floor__building")
                .filter(pk=rid)
                .first()
            )
        except (TypeError, ValueError):
            pass
    if searched_room is None and q_raw:
        base_qs = (
            Room.objects.select_related("floor", "floor__building")
            .filter(name__icontains=q_raw)
            .order_by("name")
        )
        total_matches = base_qs.count()
        if total_matches == 1:
            searched_room = base_qs.first()
        elif total_matches > 1:
            paginator = Paginator(base_qs, HOME_ROOM_SEARCH_PER_PAGE)
            room_search_page = paginator.get_page(request.GET.get("page"))

    room_blueprint_url = ""
    if searched_room:
        room_blueprint_url = room_blueprint_display_url(searched_room)

    # --- Dữ liệu dashboard (bám database) ---
    eq_total = Equipment.objects.count()
    eq_good = Equipment.objects.filter(status="good").count()
    eq_good_pct = round((eq_good / eq_total) * 100) if eq_total else 0

    inc_open = Incident.objects.filter(status="open").count()
    inc_processing = Incident.objects.filter(status="processing").count()
    inc_high_open = Incident.objects.filter(status="open", priority="high").count()

    now = timezone.now()
    q_idx = (now.month - 1) // 3
    start_month = q_idx * 3 + 1
    quarter_start = timezone.make_aware(
        datetime(now.year, start_month, 1, 0, 0, 0),
        timezone.get_current_timezone(),
    )
    incidents_closed_quarter = Incident.objects.filter(
        status="closed", reported_at__gte=quarter_start
    ).count()

    maintenance_recent = (
        Maintenance.objects.select_related("asset", "staff")
        .order_by("-maintenance_date")[:6]
    )
    incidents_recent = (
        Incident.objects.select_related("incident_type", "asset")
        .order_by("-reported_at")[:8]
    )

    room_by_type = list(
        Room.objects.values("room_type").annotate(c=Count("id")).order_by("-c")
    )
    rmax = max((x["c"] for x in room_by_type), default=0)

    room_type_labels = dict(Room.ROOM_TYPES)
    room_type_chart = []
    denom = rooms_count or 1
    for row in room_by_type:
        c = row["c"]
        code = row["room_type"]
        room_type_chart.append(
            {
                "code": code,
                "label": room_type_labels.get(code, code),
                "count": c,
                "pct": round(100 * c / denom),
            }
        )

    cost_agg = Maintenance.objects.aggregate(s=Sum("cost"))
    maintenance_cost_total = cost_agg["s"] or 0

    pending_total = inc_open + inc_processing
    pending_bar_pct = min(100, 15 + pending_total * 12) if pending_total else 12
    urgent_bar_pct = min(100, 10 + inc_high_open * 20) if inc_high_open else 8

    context = {
        "stats": {
            "branches": branches_count,
            "buildings": buildings_count,
            "rooms": rooms_count,
            "equipment": equipment_count,
            "trees": trees_count,
        },
        "is_admin": bool(
            request.user.is_authenticated
            and (request.user.is_superuser or request.user.is_staff or _is_admin_role(role_name))
        ),
        "is_facility": bool(
            request.user.is_authenticated and app_user and _is_facility_or_technical_staff(role_name)
        ),
        "is_teacher": bool(request.user.is_authenticated and app_user and _is_teacher_role(role_name)),
        "room_search_q": q_raw,
        "searched_room": searched_room,
        "room_search_page": room_search_page,
        "room_blueprint_url": room_blueprint_url,
        "eq_total": eq_total,
        "eq_good_pct": eq_good_pct,
        "inc_open": inc_open,
        "inc_processing": inc_processing,
        "inc_high_open": inc_high_open,
        "incidents_closed_quarter": incidents_closed_quarter,
        "maintenance_recent": maintenance_recent,
        "incidents_recent": incidents_recent,
        "room_by_type": room_by_type,
        "room_by_type_max": rmax,
        "room_type_chart": room_type_chart,
        "maintenance_cost_total": maintenance_cost_total,
        "pending_total": pending_total,
        "pending_bar_pct": pending_bar_pct,
        "urgent_bar_pct": urgent_bar_pct,
    }
    return render(request, "home/index.html", context)


def about_school(request):
    """Trang giới thiệu quản trị động: Hero, giá trị cốt lõi, tin tức cập nhật."""
    app_user = None
    role_name = ""
    if request.user.is_authenticated:
        app_user, role_name = _current_role_name(request)

    try:
        hero_section = AboutHeroSection.objects.filter(is_active=True).first()
    except (ProgrammingError, OperationalError):
        hero_section = None

    try:
        core_values = list(AboutCoreValue.objects.filter(is_active=True).order_by("display_order", "-updated_at"))
    except (ProgrammingError, OperationalError):
        core_values = []

    try:
        about_announcements = list(AboutAnnouncement.objects.filter(is_published=True).order_by("-created_at", "-published_at")[:5])
    except (ProgrammingError, OperationalError):
        about_announcements = []

    try:
        about_events = list(
            AboutFeaturedEvent.objects.filter(is_published=True).order_by("-created_at", "-published_at", "-event_date")[:3]
        )
    except (ProgrammingError, OperationalError):
        about_events = []

    latest_news = about_announcements[0] if about_announcements else None
    side_news = about_announcements[1:] if len(about_announcements) > 1 else []

    selected_news = None
    selected_news_pk = request.GET.get("news")
    if selected_news_pk:
        try:
            selected_news = AboutAnnouncement.objects.filter(is_published=True, pk=int(selected_news_pk)).first()
        except (TypeError, ValueError):
            selected_news = None

    context = {
        "is_admin": bool(
            request.user.is_authenticated
            and (request.user.is_superuser or request.user.is_staff or _is_admin_role(role_name))
        ),
        "is_facility": bool(
            request.user.is_authenticated and app_user and _is_facility_or_technical_staff(role_name)
        ),
        "is_teacher": bool(request.user.is_authenticated and app_user and _is_teacher_role(role_name)),
        "about_hero_section": hero_section,
        "about_core_values": core_values,
        "about_latest_news": latest_news,
        "about_side_news": side_news,
        "about_events": about_events,
        "selected_news": selected_news,
    }
    return render(request, "home/about_school.html", context)


def about_news_detail(request, pk: int):
    """Chi tiết bài tin tức thuộc trang giới thiệu."""
    article = get_object_or_404(AboutAnnouncement, pk=pk, is_published=True)
    if request.GET.get("ajax") == "1" or request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "type": "news",
                "title": article.title,
                "summary": article.summary,
                "content": article.content,
                "published_at": article.published_at.strftime("%d/%m/%Y %H:%M") if article.published_at else "",
                "thumbnail": article.thumbnail.url if article.thumbnail else None,
            }
        )
    return render(request, "home/about_news_detail.html", {"article": article})


def about_event_detail(request, pk: int):
    """Chi tiết sự kiện nổi bật thuộc trang giới thiệu."""
    event = get_object_or_404(AboutFeaturedEvent, pk=pk, is_published=True)
    if request.GET.get("ajax") == "1" or request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "type": "event",
                "title": event.title,
                "summary": event.summary,
                "content": "",
                "published_at": event.published_at.strftime("%d/%m/%Y %H:%M") if event.published_at else "",
                "event_date": event.event_date.strftime("%d/%m/%Y") if event.event_date else "",
                "image": event.image.url if event.image else None,
            }
        )
    return JsonResponse({"detail": "This endpoint supports AJAX-only event detail fetch."})


def about_updates(request):
    """Trang hiển thị toàn bộ Tin tức và Sự kiện nổi bật."""
    news_items = AboutAnnouncement.objects.filter(is_published=True).order_by("-created_at", "-published_at")
    event_items = AboutFeaturedEvent.objects.filter(is_published=True).order_by("-created_at", "-published_at", "-event_date")
    return render(
        request,
        "home/about_updates.html",
        {
            "news_items": news_items,
            "event_items": event_items,
        },
    )


class Login(LoginView):
    template_name = 'login.html'
    authentication_form = BootstrapAuthenticationForm

    def get_success_url(self):
        """
        Sau khi đăng nhập: nếu tài khoản mới tạo cần đổi mật khẩu thì đưa về trang đổi mật khẩu,
        còn không thì về trang chủ như bình thường.
        """
        app_user, role_name = _current_role_name(self.request)
        if _requires_password_change(app_user, role_name):
            return reverse("account_password_change")
        return reverse("home")


def page_not_found(request, exception=None, invalid_path=None):
    """Trang 404 thân thiện (handler404 khi DEBUG=False; catch-all khi DEBUG=True)."""
    return render(request, "errors/404.html", status=404)


PWD_SESSION_EMAIL = "pwd_reset_email"
PWD_SESSION_USER_ID = "pwd_reset_user_id"
PWD_VERIFY_ATTEMPTS = "pwd_reset_verify_attempts"
PWD_VERIFY_MAX_ATTEMPTS = 10


def _mask_email(addr: str) -> str:
    if "@" not in addr:
        return "***"
    local, _, domain = addr.partition("@")
    if len(local) <= 3:
        return "***@" + domain
    return local[:3] + "****@" + domain


def forgot_password_request(request):
    """Bước 1: nhập email → gửi mã 6 số qua Gmail/SMTP."""
    if request.method == "POST":
        form = ForgotPasswordEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            code = generate_six_digit_code()
            code_hash = hash_reset_code(email, code)
            ttl = int(getattr(settings, "PASSWORD_RESET_CODE_TTL_MINUTES", 15))
            now = timezone.now()
            PasswordResetCode.objects.filter(email=email, consumed=False).update(consumed=True)
            PasswordResetCode.objects.create(
                email=email,
                code_hash=code_hash,
                expires_at=now + timedelta(minutes=ttl),
            )
            send_password_reset_code_email(to_email=email, code=code, request=request)
            request.session[PWD_SESSION_EMAIL] = email
            request.session[PWD_VERIFY_ATTEMPTS] = 0
            return redirect("password_reset_verify")
    else:
        form = ForgotPasswordEmailForm()
    return render(request, "auth/forgot_password.html", {"form": form})


def forgot_password_verify(request):
    """Bước 2: nhập mã 6 số nhận qua email."""
    email = request.session.get(PWD_SESSION_EMAIL)
    if not email:
        messages.warning(request, "Vui lòng nhập email trường ở bước trước.")
        return redirect("password_reset")

    if request.method == "POST":
        form = VerifySixDigitForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            ch = hash_reset_code(email, code)
            now = timezone.now()
            row = (
                PasswordResetCode.objects.filter(
                    email=email,
                    code_hash=ch,
                    consumed=False,
                    expires_at__gte=now,
                )
                .order_by("-created_at")
                .first()
            )
            if row:
                row.consumed = True
                row.save(update_fields=["consumed"])
                PasswordResetCode.objects.filter(email=email, consumed=False).update(consumed=True)
                from django.contrib.auth import get_user_model

                User = get_user_model()
                user = User.objects.filter(email__iexact=email, is_active=True).first()
                if user:
                    request.session[PWD_SESSION_USER_ID] = user.pk
                    request.session.pop(PWD_VERIFY_ATTEMPTS, None)
                    return redirect("password_reset_set")
            attempts = int(request.session.get(PWD_VERIFY_ATTEMPTS, 0)) + 1
            request.session[PWD_VERIFY_ATTEMPTS] = attempts
            if attempts >= PWD_VERIFY_MAX_ATTEMPTS:
                messages.error(request, "Đã thử quá nhiều lần. Vui lòng nhập lại email để nhận mã mới.")
                request.session.pop(PWD_SESSION_EMAIL, None)
                request.session.pop(PWD_VERIFY_ATTEMPTS, None)
                return redirect("password_reset")
            form.add_error("code", "Mã không đúng hoặc đã hết hạn. Vui lòng kiểm tra email hoặc yêu cầu gửi lại.")
    else:
        form = VerifySixDigitForm()

    return render(
        request,
        "auth/forgot_password_verify.html",
        {"form": form, "email_masked": _mask_email(email)},
    )


def forgot_password_set(request):
    """Bước 3: đặt mật khẩu mới sau khi mã đúng."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    uid = request.session.get(PWD_SESSION_USER_ID)
    if not uid:
        messages.warning(request, "Phiên đặt lại mật khẩu không còn hiệu lực. Thử lại từ đầu.")
        return redirect("password_reset")

    user = User.objects.filter(pk=uid, is_active=True).first()
    if not user:
        request.session.pop(PWD_SESSION_USER_ID, None)
        return redirect("password_reset")

    if request.method == "POST":
        form = BootstrapSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            AppUser.objects.filter(username__iexact=user.username).update(
                password=user.password,
                must_change_password=False,
            )
            request.session.pop(PWD_SESSION_USER_ID, None)
            request.session.pop(PWD_SESSION_EMAIL, None)
            return redirect("password_reset_complete")
    else:
        form = BootstrapSetPasswordForm(user)

    return render(request, "auth/forgot_password_set.html", {"form": form})


def forgot_password_complete(request):
    return render(request, "auth/reset_password_done.html")


@login_required
def account_password_change(request):
    app_user, role_name = _current_role_name(request)
    is_facility = bool(app_user and _is_facility_or_technical_staff(role_name))
    is_teacher = bool(app_user and _is_teacher_role(role_name))

    if not (is_facility or is_teacher):
        return redirect("home")

    if request.method == "POST":
        form = BootstrapPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            AppUser.objects.filter(username__iexact=user.username).update(
                password=user.password,
                must_change_password=False,
            )
            messages.success(request, "Đã đổi mật khẩu thành công.")
            return redirect("facility_dashboard" if is_facility else "teacher_dashboard")
    else:
        form = BootstrapPasswordChangeForm(request.user)

    context = {
        "form": form,
        "back_url": reverse("facility_dashboard" if is_facility else "teacher_dashboard"),
        "back_label": "← Quay lại trang CSVC" if is_facility else "← Quay lại trang giảng viên",
    }
    return render(request, "auth/change_password.html", context)


@login_required
def map_view(request):
    # 1. GeoJSON khuôn viên: tòa nhà (có id để drill-down), cây, sự cố.
    # Phòng / thiết bị trên WGS84 không tải sẵn — xem theo tầng và sơ đồ trong nhà.

    buildings_geojson = buildings_geojson_dumps()
    
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
                if getattr(e, "room", None):
                    blueprint_url = room_blueprint_display_url(e.room) or ""
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

    rooms_geojson = json.dumps({"type": "FeatureCollection", "features": []})

    equipment_geojson = json.dumps({"type": "FeatureCollection", "features": []})

    branches_nav = []
    for b in UniversityBranch.objects.all().order_by("name"):
        row = {"id": b.id, "name": (b.name or "").strip() or f"Chi nhánh #{b.id}"}
        if b.geom:
            c = b.geom.centroid
            row["lat"] = c.y
            row["lng"] = c.x
        else:
            row["lat"] = None
            row["lng"] = None
        branches_nav.append(row)
    branches_nav_json = json.dumps(branches_nav, ensure_ascii=False)

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
        elif _is_facility_or_technical_staff(role_name):
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
        'branches_nav_json': branches_nav_json,
    }
    return render(request, 'home/map.html', context)


@login_required
def map_building_floors(request, building_id):
    if not Building.objects.filter(pk=building_id).exists():
        return JsonResponse({"error": "Không tìm thấy tòa nhà."}, status=404)
    return JsonResponse(floors_payload_for_building(building_id))


@login_required
def map_floor_rooms(request, floor_id):
    if not Floor.objects.filter(pk=floor_id).exists():
        return JsonResponse({"error": "Không tìm thấy tầng."}, status=404)
    return JsonResponse(floor_rooms_geojson(floor_id))


@login_required
def map_floor_equipment(request, floor_id):
    if not Floor.objects.filter(pk=floor_id).exists():
        return JsonResponse({"error": "Không tìm thấy tầng."}, status=404)
    return JsonResponse(floor_equipment_map_payload(floor_id))


@login_required
def map_room_layout(request, room_id):
    data = room_layout_payload(room_id)
    if not data:
        return JsonResponse({"error": "Không tìm thấy phòng."}, status=404)
    return JsonResponse(data)


@login_required
def map_equipment_search(request):
    """
    Tìm thiết bị theo mã / tên / loại (icontains), trả về room_id + floor_id + building_id để điều hướng drill-down.
    GET: q=..., limit= (mặc định 20, tối đa 50)
    """
    q = (request.GET.get("q") or "").strip()
    try:
        limit = int(request.GET.get("limit") or 20)
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 50))
    if not q:
        return JsonResponse({"results": []})
    qs = (
        Equipment.objects.filter(
            Q(code__icontains=q) | Q(name__icontains=q) | Q(equipment_type__icontains=q)
        )
        .select_related("room", "room__floor", "room__floor__building")
        .order_by("code")[:limit]
    )
    results = []
    for eq in qs:
        room = eq.room
        fl = room.floor if room else None
        b = fl.building if fl else None
        if not room or not fl or not b:
            continue
        results.append(
            {
                "equipment_id": eq.id,
                "code": eq.code,
                "name": eq.name or "",
                "equipment_type": eq.equipment_type or "",
                "status": eq.status or "",
                "room_id": room.id,
                "room_name": room.name or "",
                "floor_id": fl.id,
                "floor_name": fl.name or "",
                "building_id": b.id,
                "building_name": b.name or "",
            }
        )
    return JsonResponse({"results": results})


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

    if lat < 0 or lng < 0 or radius < 0:
        return JsonResponse({"error": "lat, lng và bán kính không được âm."}, status=400)

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
                    "blueprint_url": room_blueprint_display_url(obj.room) if getattr(obj, "room", None) else "",
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
                    "blueprint_url": room_blueprint_display_url(obj),
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
    GET branch_id: chỉ cây thuộc chi nhánh đó.
    """
    dangerous_trees = Tree.objects.filter(health_status="dangerous").exclude(geom__isnull=True)
    branch_raw = (request.GET.get("branch_id") or "").strip()
    if branch_raw:
        try:
            dangerous_trees = dangerous_trees.filter(university_branch_id=int(branch_raw))
        except (TypeError, ValueError):
            pass

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
    GET branch_id: chỉ thiết bị trong phòng thuộc tòa nhà của chi nhánh đó.
    """
    devices_qs = (
        Equipment.objects.exclude(geom__isnull=True)
        .exclude(status="good")
        .select_related("room", "room__floor", "room__floor__building")
    )
    branch_raw = (request.GET.get("branch_id") or "").strip()
    if branch_raw:
        try:
            devices_qs = devices_qs.filter(
                room__floor__building__university_branch_id=int(branch_raw)
            )
        except (TypeError, ValueError):
            pass

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
            "blueprint_url": room_blueprint_display_url(room) if room else "",
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

    if _requires_password_change(app_user, role_name):
        return redirect("account_password_change")

    # Nhân viên CSVC hoặc nhân viên kỹ thuật
    if not (app_user and _is_facility_or_technical_staff(role_name)):
        return redirect("home")

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

    if _requires_password_change(app_user, role_name):
        return redirect("account_password_change")

    if not (app_user and _is_facility_or_technical_staff(role_name)):
        return redirect("home")

    if request.method == "POST":
        form = FacilityIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)

            # Vị trí & liên kết phòng/tầng/tòa lấy từ tài sản — không cần chọn trên bản đồ
            asset = incident.asset
            if asset.asset_type == "equipment" and asset.equipment:
                eq = asset.equipment
                incident.geom = eq.geom
                incident.room = eq.room
                if eq.room:
                    incident.floor = eq.room.floor
                    if eq.room.floor:
                        incident.building = eq.room.floor.building
            elif asset.asset_type == "tree" and asset.tree:
                tr = asset.tree
                incident.geom = tr.geom
                incident.room = None
                incident.floor = None
                incident.building = None

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

    assets_meta = {str(a.id): a.asset_type for a in Asset.objects.only("id", "asset_type")}
    types_meta = {str(t.id): list(t.applies_to or []) for t in IncidentType.objects.only("id", "applies_to")}

    context = {
        "form": form,
        "recent_incidents": recent_incidents,
        "facility_assets_meta_json": json.dumps(assets_meta, ensure_ascii=False),
        "facility_incident_types_meta_json": json.dumps(types_meta, ensure_ascii=False),
    }
    return render(request, "home/facility_incident.html", context)


@login_required
def facility_teacher_reports_history(request):
    """
    CSVC xem lịch sử báo cáo sự cố nhanh (text) do giảng viên gửi.
    - `mark_seen`: đánh dấu tin nhắn đã được CSVC xem (dùng chung cho toàn bộ CSVC).
    - `delete`: xóa tin nhắn khỏi hệ thống.
    """
    app_user, role_name = _current_role_name(request)

    if _requires_password_change(app_user, role_name):
        return redirect("account_password_change")

    if not (app_user and _is_facility_or_technical_staff(role_name)):
        return redirect("home")

    if request.method == "POST":
        action = (request.POST.get("action") or "").strip()
        report_id = request.POST.get("report_id")
        if action and report_id:
            report = QuickIncidentReport.objects.filter(id=report_id).first()
            if report:
                if action == "mark_seen":
                    report.is_seen = True
                    report.seen_at = report.seen_at or timezone.now()
                    report.save(update_fields=["is_seen", "seen_at"])
                elif action == "delete":
                    report.delete()

        return redirect("facility_teacher_reports_history")

    latest_report = QuickIncidentReport.objects.order_by("-reported_at").first()
    reports = QuickIncidentReport.objects.order_by("-reported_at").all()

    context = {
        "reports": reports,
        "latest_report": latest_report,
    }
    return render(request, "home/facility_teacher_reports_history.html", context)


def logout_view(request):
    """
    Đăng xuất khỏi hệ thống và luôn quay về trang chủ.
    """
    logout(request)
    return redirect("home")


@login_required
def teacher_dashboard(request):
    """
    Dashboard read-only cho Giảng viên:
    - Xem danh sách phòng học và trạng thái (tốt / hỏng / đang sửa) dựa trên thiết bị trong phòng
    - Chuyển sang bản đồ để xem vị trí
    """
    app_user, role_name = _current_role_name(request)

    if _requires_password_change(app_user, role_name):
        return redirect("account_password_change")

    if not (app_user and _is_teacher_role(role_name)):
        return redirect("home")

    # Báo cáo sự cố nhanh dạng text (giảng viên gửi lên)
    latest_quick_report = (
        QuickIncidentReport.objects.filter(sender=app_user).order_by("-reported_at").first()
    )

    room_q = (request.GET.get("room_q") or "").strip()
    if request.method == "POST":
        form = TeacherQuickIncidentReportForm(request.POST)
        room_q = (request.POST.get("room_q") or room_q).strip()
        if form.is_valid():
            message = form.cleaned_data["message"].strip()
            if message:
                QuickIncidentReport.objects.create(
                    sender=app_user,
                    reporter_name=(app_user.username or request.user.username or "").strip(),
                    description=message,
                    is_seen=False,
                )
                messages.success(request, "Đã gửi báo cáo sự cố nhanh đến CSVC.")
            redir = reverse("teacher_dashboard")
            if room_q:
                redir += "?" + urlencode({"room_q": room_q})
            return redirect(redir)
    else:
        form = TeacherQuickIncidentReportForm()

    # Lấy danh sách phòng + thiết bị để tính trạng thái (lọc theo room_q)
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

        item = {
            "room": room,
            "status_label": status_label,
            "status_badge": status_badge,
        }
        if _teacher_room_status_matches(item, room_q):
            room_status_list.append(item)

    teacher_room_q_suffix = ("&" + urlencode({"room_q": room_q})) if room_q else ""

    paginator = Paginator(room_status_list, TEACHER_ROOMS_PER_PAGE)
    room_page = paginator.get_page(request.GET.get("page"))
    pad_count = max(0, TEACHER_ROOMS_PER_PAGE - len(room_page.object_list))
    room_pad_rows = [None] * pad_count

    context = {
        "room_page": room_page,
        "room_pad_rows": room_pad_rows,
        "teacher_quick_report_form": form,
        "latest_quick_report": latest_quick_report,
        "teacher_room_search_q": room_q,
        "teacher_room_q_suffix": teacher_room_q_suffix,
    }
    return render(request, "home/teacher_dashboard.html", context)