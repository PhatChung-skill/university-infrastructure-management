from django.db import models

class Floor(models.Model):
    name = models.TextField()
    level = models.IntegerField()
    # Dùng chuỗi tham chiếu 'Building' để tránh lỗi import vòng tròn
    building = models.ForeignKey('Building', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.building.name}"