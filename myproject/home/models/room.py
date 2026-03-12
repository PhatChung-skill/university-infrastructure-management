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

    # Trạng thái tổng quát của phòng (độc lập với thiết bị)
    ROOM_STATUS = [
        ("available", "Sẵn sàng sử dụng"),
        ("unavailable", "Tạm ngưng sử dụng"),
    ]

    name = models.TextField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.IntegerField(null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    geom = models.PointField(srid=4326)
    # Cột "status" đã tồn tại trong CSDL nên cần ánh xạ lại ở model.
    # Đặt default để khi tạo phòng mới luôn có giá trị, tránh lỗi NOT NULL.
    status = models.CharField(
        max_length=20,
        choices=ROOM_STATUS,
        default="available",
    )

    def __str__(self):
        return self.name
