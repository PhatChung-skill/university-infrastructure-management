from django.db import models


class PasswordResetCode(models.Model):
    """Mã 6 số gửi qua email; lưu băm, không lưu mã thô."""

    email = models.TextField(db_index=True)
    code_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_code"
        indexes = [
            models.Index(fields=["email", "consumed", "expires_at"]),
        ]

    def __str__(self):
        return f"{self.email} @ {self.created_at}"
