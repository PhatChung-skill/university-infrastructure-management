"""GeoJSON helpers for campus / drill-down map views."""
from __future__ import annotations

import json

from django.db.models import Count

from .models import Building, Floor, Room, Equipment


def buildings_feature_collection() -> dict:
    features = []
    for b in (
        Building.objects.exclude(geom__isnull=True)
        .select_related("university_branch")
        .only("id", "name", "description", "geom", "university_branch_id", "university_branch__name")
    ):
        br = b.university_branch
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(b.geom.geojson),
                "properties": {
                    "id": b.id,
                    "name": b.name or "",
                    "description": b.description or "",
                    "university_branch_id": b.university_branch_id,
                    "university_branch_name": br.name if br else "",
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def buildings_geojson_dumps() -> str:
    return json.dumps(buildings_feature_collection())


def room_blueprint_display_url(room: Room) -> str:
    if not room:
        return ""
    try:
        if getattr(room, "blueprint", None) and room.blueprint:
            return room.blueprint.url
    except ValueError:
        pass
    return ""


def floors_payload_for_building(building_id: int) -> dict:
    b = Building.objects.select_related("university_branch").filter(pk=building_id).first()
    if not b:
        return {
            "building_id": building_id,
            "building": None,
            "floors": [],
            "rooms": [],
        }
    br = b.university_branch
    building_info = {
        "id": b.id,
        "name": b.name or "",
        "description": b.description or "",
        "branch_id": b.university_branch_id,
        "branch_name": br.name if br else "",
    }
    qs = Floor.objects.filter(building_id=building_id).annotate(room_count=Count("rooms")).order_by("level", "id")
    floors = []
    for f in qs:
        floors.append(
            {
                "id": f.id,
                "name": f.name or "",
                "level": f.level,
                "room_count": f.room_count,
            }
        )
    rooms_out = []
    for room in (
        Room.objects.filter(floor__building_id=building_id)
        .select_related("floor")
        .order_by("floor__level", "floor_id", "name", "id")
    ):
        fl = room.floor
        rooms_out.append(
            {
                "id": room.id,
                "name": room.name or "",
                "floor_id": room.floor_id,
                "floor_name": fl.name if fl else "",
                "level": fl.level if fl else None,
                "building_name": b.name or "",
                "branch_name": building_info["branch_name"],
            }
        )
    return {
        "building_id": building_id,
        "building": building_info,
        "floors": floors,
        "rooms": rooms_out,
    }


def floor_rooms_geojson(floor_id: int) -> dict:
    features = []
    for room in Room.objects.filter(floor_id=floor_id).select_related("floor", "floor__building").exclude(geom__isnull=True):
        bname = room.floor.building.name if room.floor and room.floor.building else ""
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(room.geom.geojson),
                "properties": {
                    "id": room.id,
                    "name": room.name or "",
                    "room_type": room.room_type,
                    "capacity": room.capacity,
                    "floor_id": room.floor_id,
                    "floor_name": room.floor.name if room.floor else "",
                    "building_id": room.floor.building_id if room.floor else None,
                    "building_name": bname,
                    "blueprint_url": room_blueprint_display_url(room),
                    "blueprint_width": room.blueprint_width,
                    "blueprint_height": room.blueprint_height,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def floor_equipment_map_payload(floor_id: int) -> dict:
    """
    Thiết bị thuộc phòng trên tầng: GeoJSON điểm (có GPS) + danh sách đầy đủ cho panel.
    """
    features = []
    items = []
    qs = Equipment.objects.filter(room__floor_id=floor_id).select_related(
        "room", "room__floor", "room__floor__building"
    )
    for eq in qs:
        room = eq.room
        bname = room.floor.building.name if room and room.floor and room.floor.building else ""
        fname = room.floor.name if room and room.floor else ""
        rname = room.name if room else ""
        items.append(
            {
                "id": eq.id,
                "code": eq.code,
                "name": eq.name or "",
                "status": eq.status or "",
                "equipment_type": eq.equipment_type or "",
                "room_name": rname,
                "has_gps": eq.geom is not None,
            }
        )
        if eq.geom:
            features.append(
                {
                    "type": "Feature",
                    "geometry": json.loads(eq.geom.geojson),
                    "properties": {
                        "id": eq.id,
                        "code": eq.code,
                        "name": eq.name or "",
                        "status": eq.status or "",
                        "equipment_type": eq.equipment_type or "",
                        "room_name": rname,
                        "floor_name": fname,
                        "building_name": bname,
                        "blueprint_url": room_blueprint_display_url(room) if room else "",
                    },
                }
            )
    return {
        "geojson": {"type": "FeatureCollection", "features": features},
        "items": items,
    }


def room_layout_payload(room_id: int) -> dict | None:
    room = Room.objects.select_related("floor", "floor__building").filter(pk=room_id).first()
    if not room:
        return None
    w = room.blueprint_width or 800
    h = room.blueprint_height or 600
    equip_list = []
    for eq in Equipment.objects.filter(room_id=room_id):
        equip_list.append(
            {
                "id": eq.id,
                "code": eq.code,
                "name": eq.name or "",
                "equipment_type": eq.equipment_type or "",
                "status": eq.status or "",
                "local_x": eq.local_x,
                "local_y": eq.local_y,
            }
        )
    return {
        "room": {
            "id": room.id,
            "name": room.name or "",
            "room_type": room.room_type,
            "floor_name": room.floor.name if room.floor else "",
            "building_name": room.floor.building.name if room.floor and room.floor.building else "",
            "blueprint_url": room_blueprint_display_url(room),
            "blueprint_width": w,
            "blueprint_height": h,
        },
        "equipment": equip_list,
    }


def floors_meta_for_admin() -> str:
    """JSON list for room form: [{id, building_id, name, level}, ...]"""
    rows = []
    for f in Floor.objects.select_related("building").order_by("building_id", "level", "id"):
        rows.append(
            {
                "id": f.id,
                "building_id": f.building_id,
                "name": f.name or "",
                "level": f.level,
                "building_name": f.building.name if f.building else "",
            }
        )
    return json.dumps(rows, ensure_ascii=False)
