from django.db import models


class QuickIncidentReport(models.Model):
    """
    Tin nhắn báo cáo sự cố nhanh (text) do giảng viên gửi tới CSVC.
    Trạng thái xem được dùng chung theo toàn bộ CSVC thông qua `is_seen`.
    """

    sender = models.ForeignKey(
        "AppUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quick_incident_reports",
    )
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # Đã/Chưa được CSVC xem (dùng chung theo toàn bộ CSVC).
    is_seen = models.BooleanField(default=False)
    seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        preview = (self.message or "").strip().replace("\n", " ")
        if len(preview) > 30:
            preview = f"{preview[:30]}..."
        sender = self.sender.username if self.sender else "Unknown"
        return f"QuickIncidentReport #{self.id} by {sender} ({preview})"

    class Meta:
        ordering = ["-created_at"]

