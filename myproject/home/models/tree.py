from django.contrib.gis.db import models


class Tree(models.Model):
    HEALTH_STATUS = [
        ('good', 'Good'),
        ('diseased', 'Diseased'),
        ('dangerous', 'Dangerous'),
    ]

    code = models.CharField(max_length=50, unique=True)
    species = models.TextField()
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUS)
    planted_date = models.DateField(null=True, blank=True)
    last_trimmed = models.DateField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    geom = models.PointField(srid=4326)

    def __str__(self):
        return self.code
