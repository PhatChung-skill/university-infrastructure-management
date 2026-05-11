from django.db import models


class LandingHero(models.Model):
    """
    Singleton model — chỉ lưu 1 bản ghi duy nhất cho Hero Section trang giới thiệu.
    Admin có thể chỉnh sửa ảnh nền, tiêu đề và lời ngỏ bất cứ lúc nào.
    """
    title = models.CharField(
        max_length=200,
        default="Hệ thống Quản lý Cơ sở hạ tầng Đại học",
        verbose_name="Tiêu đề chính",
    )
    subtitle = models.TextField(
        default=(
            "Nền tảng số hoá toàn diện cơ sở vật chất — hướng tới môi trường "
            "học tập an toàn, minh bạch và hiệu quả cho toàn trường."
        ),
        verbose_name="Lời ngỏ / Mô tả",
    )
    background_image = models.ImageField(
        upload_to="landing/hero/",
        null=True,
        blank=True,
        verbose_name="Ảnh nền Hero (để trống → dùng gradient mặc định)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hero trang giới thiệu"
        verbose_name_plural = "Hero trang giới thiệu"

    def __str__(self) -> str:
        return self.title

    @classmethod
    def get_solo(cls) -> "LandingHero":
        """Lấy bản ghi singleton, tạo mới với giá trị mặc định nếu chưa có."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
