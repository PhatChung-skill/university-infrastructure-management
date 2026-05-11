from django.contrib.gis.db import models

class UniversityBranch(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    geom = models.PolygonField(srid=4326, blank=True, null=True)

    class Meta:
        db_table = 'university_branch'

    def __str__(self):
        return self.name

class Building(models.Model):
    name = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    geom = models.PolygonField(srid=4326, blank=True, null=True)
    university_branch = models.ForeignKey(
        UniversityBranch, on_delete=models.SET_NULL, null=True, blank=True, related_name="buildings"
    )

    class Meta:
        db_table = 'building'
        indexes = [
            models.Index(fields=['geom'], name='idx_building_geom'),
        ]

    def __str__(self):
        return self.name