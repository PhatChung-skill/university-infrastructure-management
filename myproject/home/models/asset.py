from django.db import models
from django.core.exceptions import ValidationError

class Asset(models.Model):
    ASSET_TYPES = [
        ("equipment", "Thiết bị"),
        ("tree", "Cây xanh"),
    ]

    # Dùng chuỗi tham chiếu để tránh lỗi circular import
    equipment = models.OneToOneField(
        'Equipment', on_delete=models.CASCADE, null=True, blank=True
    )
    tree = models.OneToOneField(
        'Tree', on_delete=models.CASCADE, null=True, blank=True
    )
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)

    def clean(self):
        # Dùng ValidationError để trang Admin hiển thị lỗi thân thiện với người dùng
        if (self.equipment and self.tree) or (not self.equipment and not self.tree):
            raise ValidationError("Một tài sản phải là Thiết bị HOẶC Cây xanh (Không được chọn cả hai hoặc bỏ trống cả hai).")

    def __str__(self):
        # Hiển thị thân thiện để dropdown "Tài sản" dễ chọn hơn
        if self.asset_type == "equipment" and self.equipment:
            name = (self.equipment.name or "").strip()
            suffix = f" - {name}" if name else ""
            return f"Thiết bị {self.equipment.code}{suffix}"

        if self.asset_type == "tree" and self.tree:
            species = (self.tree.species or "").strip()
            suffix = f" - {species}" if species else ""
            return f"Cây {self.tree.code}{suffix}"

        return "Tài sản"