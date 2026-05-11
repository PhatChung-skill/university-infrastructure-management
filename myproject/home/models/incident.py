from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class IncidentType(models.Model):
    APPLIES_TO_CHOICES = [
        ("equipment", "Thiết bị"),
        ("tree", "Cây xanh"),
        ("facility", "Cơ sở vật chất"),
        ("security", "An ninh"),
        ("emergency", "Khẩn cấp"),
    ]
    code = models.TextField(unique=True)
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    default_severity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    applies_to = ArrayField(
        models.CharField(max_length=20, choices=APPLIES_TO_CHOICES),
        default=list,
        blank=True,
    )

    class Meta:
        db_table = 'incident_type'

    def __str__(self):
        return self.name

    @property
    def applies_to_labels(self):
        labels_map = dict(self.APPLIES_TO_CHOICES)
        return ", ".join(labels_map.get(item, item) for item in (self.applies_to or []))

class Incident(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("processing", "Processing"),
        ("closed", "Closed"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    reported_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True)
    asset = models.ForeignKey("Asset", on_delete=models.SET_NULL, null=True, blank=True)
    building = models.ForeignKey("Building", on_delete=models.SET_NULL, null=True, blank=True)
    floor = models.ForeignKey("Floor", on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey("Room", on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, blank=True, null=True)
    incident_type = models.ForeignKey(IncidentType, on_delete=models.SET_NULL, null=True, blank=True)
    geom = models.PointField(srid=4326, blank=True, null=True)

    class Meta:
        db_table = "incident"
        indexes = [
            models.Index(fields=["geom"], name="idx_incident_geom"),
        ]

    def __str__(self):
        return self.title