from django.contrib.gis.db import models
from django.core.validators import MinValueValidator


class Room(models.Model):
    ROOM_TYPES = [
        ("classroom", "Classroom"),
        ("lab", "Lab"),
        ("library", "Library"),
        ("office", "Office"),
        ("hall", "Hall"),
    ]
    name = models.TextField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    floor = models.ForeignKey("Floor", on_delete=models.SET_NULL, null=True, blank=True, related_name="rooms")
    geom = models.PolygonField(srid=4326, blank=True, null=True)
    blueprint = models.ImageField(
        "Sơ đồ phòng",
        upload_to="room_blueprints/",
        blank=True,
        null=True,
        help_text="Hình ảnh sơ đồ / mặt bằng phòng (PNG, JPG…).",
    )
    blueprint_width = models.PositiveIntegerField(
        "Chiều rộng sơ đồ (px)",
        blank=True,
        null=True,
        help_text="Tùy chọn, dùng khi hiển thị overlay trên bản đồ nội bộ.",
    )
    blueprint_height = models.PositiveIntegerField(
        "Chiều cao sơ đồ (px)",
        blank=True,
        null=True,
        help_text="Tùy chọn.",
    )

    class Meta:
        db_table = "room"
        constraints = [
            models.UniqueConstraint(fields=["floor", "name"], name="uniq_room_name_per_floor"),
        ]
        indexes = [
            models.Index(fields=["geom"], name="idx_room_geom"),
        ]

    def __str__(self):
        return self.name