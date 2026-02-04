from django.contrib.gis.db import models


class Building(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    geom = models.PolygonField(srid=4326)

    def __str__(self):
        return self.name
