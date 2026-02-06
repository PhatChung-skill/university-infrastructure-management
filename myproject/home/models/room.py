from django.contrib.gis.db import models
from .building import Building


class Room(models.Model):
    ROOM_TYPES = [
        ("classroom", "Phòng học"),
        ("lab", "Phòng thí nghiệm"),
        ("library", "Thư viện"),
        ("office", "Văn phòng"),
        ("hall", "Hội trường"),
    ]

    name = models.TextField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.IntegerField(null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    geom = models.PointField(srid=4326)

    def __str__(self):
        return self.name
