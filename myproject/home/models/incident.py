from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class IncidentType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    default_severity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def __str__(self):
        return self.name


class Incident(models.Model):
    STATUS = [
        ("open", "Mở"),
        ("processing", "Đang xử lý"),
        ("closed", "Đã đóng"),
    ]

    PRIORITY = [
        ("low", "Thấp"),
        ("medium", "Trung bình"),
        ("high", "Cao"),
    ]

    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY, null=True, blank=True)
    
    # CẬP NHẬT: Đổi từ CASCADE sang SET NULL theo cấu trúc database mới
    asset = models.ForeignKey('Asset', on_delete=models.SET_NULL, null=True, blank=True)
    incident_type = models.ForeignKey('IncidentType', on_delete=models.SET_NULL, null=True)
    geom = models.PointField(srid=4326, null=True, blank=True)

    def __str__(self):
        return self.title if self.title else f"Sự cố #{self.id}"