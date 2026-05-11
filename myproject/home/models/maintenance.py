from django.contrib.gis.db import models
from django.core.validators import MinValueValidator


class Maintenance(models.Model):
    MAINTENANCE_TYPES = [
        ("repair", "Repair"),
        ("inspection", "Inspection"),
        ("trim", "Trim"),
        ("replace", "Replace"),
    ]
    asset = models.ForeignKey("Asset", on_delete=models.SET_NULL, null=True, blank=True)
    staff = models.ForeignKey("AppUser", on_delete=models.SET_NULL, null=True, blank=True)
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    maintenance_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "maintenance"

    def __str__(self):
        if self.asset_id and self.asset:
            return f"{self.asset} - {self.get_maintenance_type_display()}"
        return f"Bảo trì #{self.pk}"