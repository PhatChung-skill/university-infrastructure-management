from django.contrib.gis.db import models
from django.db.models import Q


class Asset(models.Model):
    ASSET_TYPES = [
        ("equipment", "Equipment"),
        ("tree", "Tree"),
    ]
    equipment = models.ForeignKey("Equipment", on_delete=models.SET_NULL, null=True, blank=True)
    tree = models.ForeignKey("Tree", on_delete=models.SET_NULL, null=True, blank=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)

    class Meta:
        db_table = "asset"
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(equipment__isnull=False) & Q(tree__isnull=True)) |
                    (Q(equipment__isnull=True) & Q(tree__isnull=False))
                ),
                name="check_asset_type_exclusive"
            )
        ]

    def __str__(self):
        if self.asset_type == "equipment" and self.equipment:
            return f"Thiết bị: {self.equipment}"
        if self.asset_type == "tree" and self.tree:
            return f"Cây: {self.tree}"
        return f"Tài sản #{self.id}"

    @property
    def university_branch(self):
        """Chi nhánh theo cây hoặc theo tòa của phòng gắn thiết bị."""
        if self.asset_type == "tree" and self.tree_id:
            t = self.tree
            return t.university_branch if t else None
        if self.asset_type == "equipment" and self.equipment_id:
            eq = self.equipment
            room = getattr(eq, "room", None) if eq else None
            fl = getattr(room, "floor", None) if room else None
            b = getattr(fl, "building", None) if fl else None
            return b.university_branch if b else None
        return None