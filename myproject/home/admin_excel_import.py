from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
import unicodedata

from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Q

from .models import AppUser, Asset, Building, Equipment, Floor, Incident, IncidentType, Maintenance, Room, Tree, UniversityBranch


@dataclass
class ImportResult:
    created_count: int
    errors: list[str]


def _to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    cleaned = str(value).strip()
    return cleaned or None


def _to_int(value: Any) -> int | None:
    text = _to_text(value)
    if text is None:
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    text = _to_text(value)
    if text is None:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _validate_lat_lng_non_negative(
    lat: float | None, lng: float | None, row_number: int, errors: list[str]
) -> None:
    """Khi đủ cặp lat/lng, không cho âm (phạm vi hiển thị VN)."""
    if lat is None or lng is None:
        return
    if lat < 0 or lng < 0:
        errors.append(f"Dòng {row_number}: vĩ độ và kinh độ không được âm.")


def _validate_local_xy_non_negative(
    local_x: float | None, local_y: float | None, row_number: int, errors: list[str]
) -> None:
    if local_x is not None and local_x < 0:
        errors.append(f"Dòng {row_number}: local_x không được âm.")
    if local_y is not None and local_y < 0:
        errors.append(f"Dòng {row_number}: local_y không được âm.")


def _to_decimal(value: Any) -> Decimal | None:
    text = _to_text(value)
    if text is None:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _to_text(value)
    if text is None:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    text = _to_text(value)
    if text is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


TABLE_IMPORT_CONFIG: dict[str, dict[str, Any]] = {
    "equipment": {
        "columns": [
            "code",
            "name",
            "equipment_type",
            "status",
            "room_id",
            "install_date",
            "last_maintenance",
            "lat",
            "lng",
            "local_x",
            "local_y",
        ],
        "required": ["code", "name", "equipment_type", "status", "room_id"],
    },
    "tree": {
        "columns": [
            "code",
            "species",
            "height",
            "health_status",
            "planted_date",
            "last_trimmed",
            "note",
            "university_branch_id",
            "lat",
            "lng",
        ],
        "required": ["code", "species", "health_status", "university_branch_id"],
    },
    "incident": {
        "columns": [
            "title",
            "description",
            "status",
            "priority",
            "reported_at",
            "asset_id",
            "equipment_code",
            "building_id",
            "floor_id",
            "room_id",
            "incident_type_id",
            "lat",
            "lng",
        ],
        "required": ["title", "status", "priority"],
    },
    "maintenance": {
        "columns": [
            "asset_id",
            "staff_id",
            "maintenance_type",
            "maintenance_date",
            "cost",
            "note",
        ],
        "required": ["asset_id", "maintenance_type"],
    },
}


def _normalize_text(value: Any) -> str:
    text = _to_text(value) or ""
    normalized = unicodedata.normalize("NFD", text)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return normalized.lower().strip()


def _resolve_room(value: Any) -> Room | None:
    raw = _to_text(value)
    if raw is None:
        return None
    room_id = _to_int(raw)
    if room_id is not None:
        return Room.objects.filter(pk=room_id).first()
    by_name = list(Room.objects.filter(name__iexact=raw).select_related("floor", "floor__building")[:2])
    if len(by_name) == 1:
        return by_name[0]
    return None


def _resolve_branch(value: Any) -> UniversityBranch | None:
    raw = _to_text(value)
    if raw is None:
        return None
    branch_id = _to_int(raw)
    if branch_id is not None:
        return UniversityBranch.objects.filter(pk=branch_id).first()
    branches = list(UniversityBranch.objects.all()[:500])
    target = _normalize_text(raw)
    for branch in branches:
        if _normalize_text(branch.name) == target:
            return branch
    return None


def _resolve_maintenance_type(value: Any) -> str | None:
    raw = _to_text(value)
    if raw is None:
        return None
    normalized = _normalize_text(raw)
    code_map = {
        "repair": "repair",
        "inspection": "inspection",
        "trim": "trim",
        "replace": "replace",
    }
    label_map = {
        "repair": "repair",
        "inspection": "inspection",
        "trim": "trim",
        "replace": "replace",
        "sua chua": "repair",
        "kiem tra": "inspection",
        "cat tia": "trim",
        "thay the": "replace",
    }
    return code_map.get(normalized) or label_map.get(normalized)


def _resolve_asset(value: Any) -> Asset | None:
    raw = _to_text(value)
    if raw is None:
        return None

    asset_id = _to_int(raw)
    if asset_id is not None:
        return Asset.objects.filter(pk=asset_id).select_related("equipment", "tree").first()

    # Cho phep nhap theo ma/ten thiet bi
    equipment_qs = Equipment.objects.filter(Q(code__iexact=raw) | Q(name__iexact=raw))
    if equipment_qs.count() == 1:
        equipment = equipment_qs.first()
        asset = Asset.objects.filter(asset_type="equipment", equipment=equipment).first()
        if asset is None:
            asset = Asset.objects.create(asset_type="equipment", equipment=equipment)
        return asset

    # Cho phep nhap theo ma cay
    tree_qs = Tree.objects.filter(code__iexact=raw)
    if tree_qs.count() == 1:
        tree = tree_qs.first()
        asset = Asset.objects.filter(asset_type="tree", tree=tree).first()
        if asset is None:
            asset = Asset.objects.create(asset_type="tree", tree=tree)
        return asset

    return None


def _resolve_staff(value: Any) -> AppUser | None:
    raw = _to_text(value)
    if raw is None:
        return None

    staff_id = _to_int(raw)
    if staff_id is not None:
        return AppUser.objects.filter(pk=staff_id).first()

    qs = AppUser.objects.filter(Q(username__iexact=raw) | Q(email__iexact=raw))
    if qs.count() == 1:
        return qs.first()
    return None


def _validate_headers(headers: list[Any], table_name: str) -> tuple[dict[str, int], list[str]]:
    config = TABLE_IMPORT_CONFIG[table_name]
    expected_columns = config["columns"]
    normalized = [_to_text(h).lower() if _to_text(h) else "" for h in headers]
    header_map = {name: idx for idx, name in enumerate(normalized) if name}
    missing = [col for col in expected_columns if col not in header_map]
    errors = []
    if missing:
        errors.append(f"Thiếu cột trong file Excel: {', '.join(missing)}")
    return header_map, errors


def import_rows_from_workbook(table_name: str, workbook) -> ImportResult:
    if table_name not in TABLE_IMPORT_CONFIG:
        return ImportResult(created_count=0, errors=["Bảng nhập không hợp lệ."])

    errors: list[str] = []
    created_count = 0
    sheet = workbook[table_name] if table_name in workbook.sheetnames else workbook.active

    all_rows = list(sheet.iter_rows(values_only=True))
    if not all_rows:
        return ImportResult(created_count=0, errors=["File Excel không có dữ liệu."])

    headers = all_rows[0]
    header_map, header_errors = _validate_headers(list(headers), table_name)
    if header_errors:
        return ImportResult(created_count=0, errors=header_errors)

    config = TABLE_IMPORT_CONFIG[table_name]
    required_columns = config["required"]

    with transaction.atomic():
        for row_number, values in enumerate(all_rows[1:], start=2):
            if not values or all(_to_text(v) is None for v in values):
                continue

            row_data: dict[str, Any] = {}
            row_error_start = len(errors)
            for col in config["columns"]:
                idx = header_map[col]
                row_data[col] = values[idx] if idx < len(values) else None

            for req_col in required_columns:
                if _to_text(row_data.get(req_col)) is None:
                    errors.append(f"Dòng {row_number}: Cột '{req_col}' không được để trống.")

            if table_name == "equipment":
                _handle_equipment_row(row_data, row_number, errors)
            elif table_name == "tree":
                _handle_tree_row(row_data, row_number, errors)
            elif table_name == "incident":
                _handle_incident_row(row_data, row_number, errors)
            elif table_name == "maintenance":
                _handle_maintenance_row(row_data, row_number, errors)
            if len(errors) == row_error_start:
                created_count += 1

        if errors:
            transaction.set_rollback(True)
            return ImportResult(created_count=0, errors=errors)

    return ImportResult(created_count=created_count, errors=[])


def _handle_equipment_row(row_data: dict[str, Any], row_number: int, errors: list[str]) -> None:
    row_error_count = len(errors)
    code = _to_text(row_data.get("code"))
    name = _to_text(row_data.get("name"))
    equipment_type = _to_text(row_data.get("equipment_type"))
    status = _to_text(row_data.get("status"))
    room_id = _to_int(row_data.get("room_id"))

    if status and status not in dict(Equipment.STATUS_CHOICES):
        errors.append(f"Dòng {row_number}: status '{status}' không hợp lệ.")
    room = _resolve_room(row_data.get("room_id"))
    if _to_text(row_data.get("room_id")) and not room:
        errors.append(f"Dòng {row_number}: room_id phải là ID phòng hợp lệ hoặc tên phòng duy nhất.")
    if code and Equipment.objects.filter(code=code).exists():
        errors.append(f"Dòng {row_number}: code '{code}' đã tồn tại.")

    lat = _to_float(row_data.get("lat"))
    lng = _to_float(row_data.get("lng"))
    if (lat is None) != (lng is None):
        errors.append(f"Dòng {row_number}: lat/lng phải có đủ cả cặp hoặc để trống cả hai.")
    _validate_lat_lng_non_negative(lat, lng, row_number, errors)
    geom = Point(lng, lat, srid=4326) if lat is not None and lng is not None else None

    install_date = _to_date(row_data.get("install_date"))
    if _to_text(row_data.get("install_date")) and install_date is None:
        errors.append(f"Dòng {row_number}: install_date sai định dạng ngày.")
    last_maintenance = _to_date(row_data.get("last_maintenance"))
    if _to_text(row_data.get("last_maintenance")) and last_maintenance is None:
        errors.append(f"Dòng {row_number}: last_maintenance sai định dạng ngày.")

    local_x = _to_float(row_data.get("local_x"))
    if _to_text(row_data.get("local_x")) and local_x is None:
        errors.append(f"Dòng {row_number}: local_x phải là số.")
    local_y = _to_float(row_data.get("local_y"))
    if _to_text(row_data.get("local_y")) and local_y is None:
        errors.append(f"Dòng {row_number}: local_y phải là số.")
    _validate_local_xy_non_negative(local_x, local_y, row_number, errors)

    if len(errors) > row_error_count:
        return
    Equipment.objects.create(
        code=code,
        name=name,
        equipment_type=equipment_type,
        status=status,
        room=room,
        install_date=install_date,
        last_maintenance=last_maintenance,
        geom=geom,
        local_x=local_x,
        local_y=local_y,
    )


def _handle_tree_row(row_data: dict[str, Any], row_number: int, errors: list[str]) -> None:
    row_error_count = len(errors)
    code = _to_text(row_data.get("code"))
    species = _to_text(row_data.get("species"))
    health_status = _to_text(row_data.get("health_status"))
    branch_input = row_data.get("university_branch_id")
    if health_status and health_status not in dict(Tree.HEALTH_STATUS):
        errors.append(f"Dòng {row_number}: health_status '{health_status}' không hợp lệ.")
    if code and Tree.objects.filter(code=code).exists():
        errors.append(f"Dòng {row_number}: code '{code}' đã tồn tại.")

    branch = _resolve_branch(branch_input)
    if _to_text(branch_input) and not branch:
        errors.append(f"Dòng {row_number}: university_branch_id không khớp ID hoặc tên chi nhánh.")

    lat = _to_float(row_data.get("lat"))
    lng = _to_float(row_data.get("lng"))
    if (lat is None) != (lng is None):
        errors.append(f"Dòng {row_number}: lat/lng phải có đủ cả cặp hoặc để trống cả hai.")
    _validate_lat_lng_non_negative(lat, lng, row_number, errors)
    geom = Point(lng, lat, srid=4326) if lat is not None and lng is not None else None

    height = _to_decimal(row_data.get("height"))
    if _to_text(row_data.get("height")) and height is None:
        errors.append(f"Dòng {row_number}: height phải là số.")

    planted_date = _to_date(row_data.get("planted_date"))
    if _to_text(row_data.get("planted_date")) and planted_date is None:
        errors.append(f"Dòng {row_number}: planted_date sai định dạng ngày.")
    last_trimmed = _to_date(row_data.get("last_trimmed"))
    if _to_text(row_data.get("last_trimmed")) and last_trimmed is None:
        errors.append(f"Dòng {row_number}: last_trimmed sai định dạng ngày.")

    if len(errors) > row_error_count:
        return
    Tree.objects.create(
        code=code,
        species=species,
        height=height,
        health_status=health_status,
        planted_date=planted_date,
        last_trimmed=last_trimmed,
        note=_to_text(row_data.get("note")),
        university_branch=branch,
        geom=geom,
    )


def _handle_incident_row(row_data: dict[str, Any], row_number: int, errors: list[str]) -> None:
    row_error_count = len(errors)
    title = _to_text(row_data.get("title"))
    status = _to_text(row_data.get("status"))
    priority = _to_text(row_data.get("priority"))
    if status and status not in dict(Incident.STATUS_CHOICES):
        errors.append(f"Dòng {row_number}: status '{status}' không hợp lệ.")
    if priority and priority not in dict(Incident.PRIORITY_CHOICES):
        errors.append(f"Dòng {row_number}: priority '{priority}' không hợp lệ.")

    asset_id = _to_int(row_data.get("asset_id"))
    equipment_code = _to_text(row_data.get("equipment_code"))
    building_id = _to_int(row_data.get("building_id"))
    floor_id = _to_int(row_data.get("floor_id"))
    room_id = _to_int(row_data.get("room_id"))
    incident_type_id = _to_int(row_data.get("incident_type_id"))
    asset = Asset.objects.filter(pk=asset_id).first() if asset_id else None
    incident_type = IncidentType.objects.filter(pk=incident_type_id).first() if incident_type_id else None

    building = Building.objects.filter(pk=building_id).first() if building_id else None
    floor = Floor.objects.filter(pk=floor_id).first() if floor_id else None
    room = Room.objects.filter(pk=room_id).first() if room_id else None
    if asset_id and not asset:
        errors.append(f"Dòng {row_number}: asset_id={asset_id} không tồn tại.")
    if equipment_code:
        equipment = Equipment.objects.filter(code=equipment_code).select_related("room", "room__floor", "room__floor__building").first()
        if not equipment:
            errors.append(f"Dòng {row_number}: equipment_code='{equipment_code}' không tồn tại.")
        else:
            asset = Asset.objects.filter(asset_type="equipment", equipment=equipment).first()
            if asset is None:
                asset = Asset.objects.create(asset_type="equipment", equipment=equipment)
            if equipment.room:
                room = equipment.room
                floor = equipment.room.floor
                building = floor.building if floor else None
    if building_id and not building:
        errors.append(f"Dòng {row_number}: building_id={building_id} không tồn tại.")
    if floor_id and not floor:
        errors.append(f"Dòng {row_number}: floor_id={floor_id} không tồn tại.")
    if room_id and not room:
        errors.append(f"Dòng {row_number}: room_id={room_id} không tồn tại.")
    if incident_type_id and not incident_type:
        errors.append(f"Dòng {row_number}: incident_type_id={incident_type_id} không tồn tại.")

    lat = _to_float(row_data.get("lat"))
    lng = _to_float(row_data.get("lng"))
    if (lat is None) != (lng is None):
        errors.append(f"Dòng {row_number}: lat/lng phải có đủ cả cặp hoặc để trống cả hai.")
    _validate_lat_lng_non_negative(lat, lng, row_number, errors)
    geom = Point(lng, lat, srid=4326) if lat is not None and lng is not None else None

    has_reference = bool(asset or building or floor or room or geom)
    if not has_reference:
        errors.append(f"Dòng {row_number}: cần ít nhất 1 thông tin vị trí/tài sản (asset_id/building_id/floor_id/room_id/lat+lng).")

    reported_at = _to_datetime(row_data.get("reported_at"))
    if _to_text(row_data.get("reported_at")) and reported_at is None:
        errors.append(f"Dòng {row_number}: reported_at sai định dạng ngày giờ.")

    if len(errors) > row_error_count:
        return
    Incident.objects.create(
        title=title,
        description=_to_text(row_data.get("description")),
        reported_at=reported_at,
        status=status,
        asset=asset,
        building=building,
        floor=floor,
        room=room,
        priority=priority,
        incident_type=incident_type,
        geom=geom,
    )


def _handle_maintenance_row(row_data: dict[str, Any], row_number: int, errors: list[str]) -> None:
    row_error_count = len(errors)
    maintenance_type = _resolve_maintenance_type(row_data.get("maintenance_type"))
    if _to_text(row_data.get("maintenance_type")) and not maintenance_type:
        errors.append(f"Dòng {row_number}: maintenance_type không hợp lệ. Chấp nhận repair/inspection/trim/replace hoặc tên tiếng Việt.")

    raw_asset = row_data.get("asset_id")
    asset = _resolve_asset(raw_asset)
    if _to_text(raw_asset) and not asset:
        errors.append(
            f"Dòng {row_number}: asset_id không hợp lệ. Có thể nhập ID asset, mã thiết bị, tên thiết bị hoặc mã cây."
        )

    raw_staff = row_data.get("staff_id")
    staff = _resolve_staff(raw_staff)
    if _to_text(raw_staff) and not staff:
        errors.append(f"Dòng {row_number}: staff_id không hợp lệ. Có thể nhập ID, username hoặc email nhân viên.")

    maintenance_date = _to_date(row_data.get("maintenance_date"))
    if _to_text(row_data.get("maintenance_date")) and maintenance_date is None:
        errors.append(f"Dòng {row_number}: maintenance_date sai định dạng ngày.")

    cost = _to_decimal(row_data.get("cost"))
    if _to_text(row_data.get("cost")) and cost is None:
        errors.append(f"Dòng {row_number}: cost phải là số.")

    if len(errors) > row_error_count:
        return
    Maintenance.objects.create(
        asset=asset,
        staff=staff,
        maintenance_type=maintenance_type,
        maintenance_date=maintenance_date,
        cost=cost,
        note=_to_text(row_data.get("note")),
    )
