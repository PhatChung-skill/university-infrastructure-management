from django.contrib.gis.db import models

class Equipment(models.Model):
    STATUS = [
        ("good", "Tốt"),
        ("broken", "Hỏng"),
        ("maintenance", "Đang sửa"),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.TextField(null=True, blank=True)
    equipment_type = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, null=True, blank=True)
    install_date = models.DateField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    
    # Đã chuyển thành CASCADE theo CSDL mới
    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    
    # Các trường mới cho chức năng bản đồ trong nhà (Indoor Mapping)
    local_x = models.IntegerField(null=True, blank=True)
    local_y = models.IntegerField(null=True, blank=True)
    
    geom = models.PointField(srid=4326, null=True, blank=True)

    def __str__(self):
        return self.name if self.name else self.code