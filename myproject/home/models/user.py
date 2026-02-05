from django.db import models
from django.contrib.auth.hashers import make_password


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class AppUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.TextField()
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        """
        Tự động mã hóa mật khẩu nếu đang ở dạng plain-text.

        - Nếu mật khẩu đã được Django hash (bắt đầu bằng tên thuật toán như 'pbkdf2_', 'argon2', 'bcrypt')
          thì giữ nguyên.
        - Nếu là chuỗi plain-text thì dùng make_password để mã hóa trước khi lưu.
        """
        if self.password and not (
            self.password.startswith("pbkdf2_")
            or self.password.startswith("argon2")
            or self.password.startswith("bcrypt")
        ):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
