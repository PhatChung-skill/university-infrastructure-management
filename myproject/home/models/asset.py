from django.db import models
from .equipment import Equipment
from .tree import Tree


class Asset(models.Model):
    ASSET_TYPES = [
        ('equipment', 'Equipment'),
        ('tree', 'Tree'),
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
        return f"{self.asset_type} asset"
