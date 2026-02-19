from django.contrib.gis.db import models
from .room import Room


class Equipment(models.Model):
    STATUS = [
        ("good", "Tốt"),
        ("broken", "Hỏng"),
        ("maintenance", "Đang sửa"),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.TextField()
    equipment_type = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS)
    install_date = models.DateField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    geom = models.PointField(srid=4326)

    def __str__(self):
        return self.code
