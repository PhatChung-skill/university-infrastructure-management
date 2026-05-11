from django.contrib.gis.db import models
from django.core.validators import MinValueValidator


class Tree(models.Model):
    HEALTH_STATUS = [
        ("good", "Good"),
        ("diseased", "Diseased"),
        ("dangerous", "Dangerous"),
    ]
    code = models.TextField(unique=True)
    species = models.TextField(blank=True, null=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUS, blank=True, null=True)
    planted_date = models.DateField(blank=True, null=True)
    last_trimmed = models.DateField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    university_branch = models.ForeignKey("UniversityBranch", on_delete=models.SET_NULL, null=True, blank=True, related_name="trees")
    geom = models.PointField(srid=4326, blank=True, null=True)

    class Meta:
        db_table = "tree"
        indexes = [
            models.Index(fields=["geom"], name="idx_tree_geom"),
        ]

    def __str__(self):
        return self.code