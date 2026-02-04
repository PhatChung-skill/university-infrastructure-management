from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .asset import Asset


class IncidentType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    default_severity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def __str__(self):
        return self.name


class Incident(models.Model):
    STATUS = [
        ('open', 'Open'),
        ('processing', 'Processing'),
        ('closed', 'Closed'),
    ]

    PRIORITY = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS)
    priority = models.CharField(max_length=20, choices=PRIORITY)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    incident_type = models.ForeignKey(IncidentType, on_delete=models.SET_NULL, null=True)
    geom = models.PointField(srid=4326)

    def __str__(self):
        return self.title
