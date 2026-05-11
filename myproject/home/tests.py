from django.test import TestCase
from home.admin_forms import IncidentAdminForm
from home.models import (
    UniversityBranch,
    Building,
    Floor,
    Room,
    Equipment,
    Asset,
    IncidentType,
)


class IncidentAdminFormTests(TestCase):
    def setUp(self):
        self.branch = UniversityBranch.objects.create(name="CN1")
        self.building = Building.objects.create(name="B1", university_branch=self.branch)
        self.floor = Floor.objects.create(name="T1", level=1, building=self.building)
        self.room = Room.objects.create(name="P101", room_type="classroom", floor=self.floor)
        self.equipment = Equipment.objects.create(code="EQ1", name="Máy chiếu", room=self.room)
        self.asset_equipment = Asset.objects.create(asset_type="equipment", equipment=self.equipment)
        self.it_emergency = IncidentType.objects.create(
            code="IT-EM", name="Khẩn cấp chung", applies_to=["emergency"], default_severity=5
        )
        self.it_equipment = IncidentType.objects.create(
            code="IT-EQ", name="Sự cố thiết bị", applies_to=["equipment"], default_severity=3
        )
        self.it_security = IncidentType.objects.create(
            code="IT-SEC", name="Sự cố an ninh", applies_to=["security"], default_severity=4
        )

    def test_location_only_allows_emergency_incident_type(self):
        form = IncidentAdminForm(
            data={
                "title": "Test",
                "description": "x",
                "status": "open",
                "priority": "high",
                "asset": "",
                "building": str(self.building.id),
                "floor": str(self.floor.id),
                "room": str(self.room.id),
                "incident_type": str(self.it_equipment.id),
                "latitude": "10.8",
                "longitude": "106.6",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("incident_type", form.errors)

    def test_equipment_asset_autofills_location(self):
        form = IncidentAdminForm(
            data={
                "title": "Test asset",
                "description": "x",
                "status": "open",
                "priority": "medium",
                "asset": str(self.asset_equipment.id),
                "building": "",
                "floor": "",
                "room": "",
                "incident_type": str(self.it_equipment.id),
                "latitude": "10.8",
                "longitude": "106.6",
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data["building"], self.building)
        self.assertEqual(form.cleaned_data["floor"], self.floor)
        self.assertEqual(form.cleaned_data["room"], self.room)

    def test_equipment_asset_allows_security_incident_type(self):
        form = IncidentAdminForm(
            data={
                "title": "An ninh thiết bị",
                "description": "x",
                "status": "open",
                "priority": "high",
                "asset": str(self.asset_equipment.id),
                "building": "",
                "floor": "",
                "room": "",
                "incident_type": str(self.it_security.id),
                "latitude": "10.8",
                "longitude": "106.6",
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
