from django.contrib.gis.db import models


class QuickIncidentReport(models.Model):
    reporter_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    photo = models.ImageField(upload_to="incidents/", blank=True, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    geom = models.PointField(srid=4326, blank=True, null=True)
    # Báo cáo nhanh dạng text từ giảng viên (bổ sung cho luồng CSVC)
    sender = models.ForeignKey(
        "AppUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quick_incident_reports",
    )
    is_seen = models.BooleanField(default=False)
    seen_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "quick_incident_report"

    def __str__(self):
        return f"Báo cáo nhanh - {self.reported_at.strftime('%d/%m/%Y')}"