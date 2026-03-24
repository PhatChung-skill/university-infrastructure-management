from django.contrib.gis.db import models

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
    
    # 1. Đã thay đổi liên kết từ Building sang Floor
    floor = models.ForeignKey('Floor', on_delete=models.CASCADE)
    
    # 2. Các trường mới phục vụ hiển thị bản đồ trong nhà
    blueprint_url = models.TextField(null=True, blank=True)
    blueprint_width = models.IntegerField(null=True, blank=True)
    blueprint_height = models.IntegerField(null=True, blank=True)
    
    # 3. Đã thay đổi kiểu không gian từ Point sang Polygon
    geom = models.PolygonField(srid=4326)

    def __str__(self):
        return self.name