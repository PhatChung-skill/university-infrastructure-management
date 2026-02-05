from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.gis.admin import GISModelAdmin
from .models import (
    Role, AppUser, Building, Room, Tree, Equipment,
    Asset, IncidentType, Incident, Maintenance
)

# 1. Các Model KHÔNG CÓ bản đồ (Dùng admin.ModelAdmin thường)
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role')
    list_filter = ('role',)

    def save_model(self, request, obj, form, change):
        """
        Mỗi khi bạn tạo / sửa AppUser trong Django Admin:
        - Đồng bộ sang bảng User mặc định của Django để dùng cho đăng nhập (/login/)
        - AppUser.password đã được hash trong model, nên copy thẳng sang User.password
        """
        super().save_model(request, obj, form, change)

        # Tạo (hoặc lấy) user tương ứng trong bảng auth_user
        user, created = User.objects.get_or_create(username=obj.username)
        user.password = obj.password  # đã hash từ AppUser.save()
        user.is_active = True

        # Nếu role là Admin thì cho quyền staff để vào /admin/ nếu cần
        if obj.role and obj.role.name.lower() == "admin":
            user.is_staff = True
        user.save()

@admin.register(IncidentType)
class IncidentTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'default_severity')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset_type', 'get_asset_name')
    list_filter = ('asset_type',)
    
    def get_asset_name(self, obj):
        return str(obj)
    get_asset_name.short_description = "Tên tài sản"

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('maintenance_type', 'maintenance_date', 'asset', 'cost')
    list_filter = ('maintenance_type', 'maintenance_date')

# 2. Các Model CÓ bản đồ (Dùng GISModelAdmin)
# GISModelAdmin sẽ tự động hiển thị bản đồ OpenStreetMap để bạn chấm điểm/vẽ hình

@admin.register(Building)
class BuildingAdmin(GISModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Room)
class RoomAdmin(GISModelAdmin):
    list_display = ('name', 'room_type', 'building', 'capacity')
    list_filter = ('room_type', 'building')
    search_fields = ('name',)

@admin.register(Tree)
class TreeAdmin(GISModelAdmin):
    list_display = ('code', 'species', 'health_status', 'height')
    list_filter = ('health_status', 'species')
    search_fields = ('code', 'species')

@admin.register(Equipment)
class EquipmentAdmin(GISModelAdmin):
    list_display = ('code', 'name', 'equipment_type', 'status', 'room')
    list_filter = ('status', 'equipment_type')
    search_fields = ('code', 'name')

@admin.register(Incident)
class IncidentAdmin(GISModelAdmin):
    list_display = ('title', 'status', 'priority', 'reported_at', 'incident_type')
    list_filter = ('status', 'priority', 'incident_type')
    search_fields = ('title', 'description')