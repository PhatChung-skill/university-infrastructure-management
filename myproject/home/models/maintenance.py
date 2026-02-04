from django.db import models
from .asset import Asset
from .user import AppUser


class Maintenance(models.Model):
    MAINTENANCE_TYPES = [
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
        ('trim', 'Trim'),
        ('replace', 'Replace'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    staff = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True)
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    maintenance_date = models.DateField()
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.maintenance_type} - {self.asset_id}"
