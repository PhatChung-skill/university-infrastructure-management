from django.db import models

class Maintenance(models.Model):
    MAINTENANCE_TYPES = [
        ("repair", "Sửa chữa"),
        ("inspection", "Kiểm tra"),
        ("trim", "Cắt tỉa"),
        ("replace", "Thay thế"),
    ]

    # Dùng chuỗi tham chiếu để tránh lỗi circular import
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    staff = models.ForeignKey('AppUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    maintenance_date = models.DateField()
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        # Sử dụng get_maintenance_type_display() để hiển thị nhãn tiếng Việt thay vì mã tiếng Anh
        return f"{self.get_maintenance_type_display()} - {self.asset}"