from django.db import models
from .equipment import Equipment
from .tree import Tree


class Asset(models.Model):
    ASSET_TYPES = [
        ("equipment", "Thiết bị"),
        ("tree", "Cây xanh"),
    ]

    equipment = models.OneToOneField(
        Equipment, on_delete=models.CASCADE, null=True, blank=True
    )
    tree = models.OneToOneField(
        Tree, on_delete=models.CASCADE, null=True, blank=True
    )
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)

    def clean(self):
        if (self.equipment and self.tree) or (not self.equipment and not self.tree):
            raise ValueError("Asset must reference either equipment OR tree")

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
