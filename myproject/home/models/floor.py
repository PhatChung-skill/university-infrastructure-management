from django.contrib.gis.db import models
from django.core.validators import MinValueValidator


class Floor(models.Model):
    name = models.CharField(max_length=100)
    level = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, null=True)
    building = models.ForeignKey("home.Building", on_delete=models.CASCADE, related_name="floors", null=True, blank=True)

    class Meta:
        db_table = "floor"
        constraints = [
            models.UniqueConstraint(fields=["building", "name"], name="uniq_floor_name_per_building"),
            models.UniqueConstraint(fields=["building", "level"], name="uniq_floor_level_per_building"),
        ]

    def __str__(self):
        return f"{self.name} - {self.building.name}"