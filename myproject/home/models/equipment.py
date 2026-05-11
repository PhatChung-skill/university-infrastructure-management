from django.contrib.gis.db import models


class Equipment(models.Model):
    STATUS_CHOICES = [
        ("good", "Good"),
        ("broken", "Broken"),
        ("maintenance", "Maintenance"),
    ]
    code = models.TextField(unique=True)
    name = models.TextField(blank=True, null=True)
    equipment_type = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True)
    install_date = models.DateField(blank=True, null=True)
    last_maintenance = models.DateField(blank=True, null=True)
    room = models.ForeignKey("Room", on_delete=models.SET_NULL, null=True, blank=True, related_name="equipment_set")
    geom = models.PointField(srid=4326, blank=True, null=True)
    # Tọa độ pixel trên sơ đồ phòng (góc trên-trái = 0,0) — dùng với CRS.Simple trên bản đồ công khai / quản trị
    local_x = models.FloatField(blank=True, null=True)
    local_y = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "equipment"
        indexes = [
            models.Index(fields=["geom"], name="idx_equipment_geom"),
        ]

    def __str__(self):
        return self.name or self.code