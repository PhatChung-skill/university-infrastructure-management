from django.db import models


class LandingGridItem(models.Model):
    """
    Mỗi bản ghi là 1 cột/thẻ trong lưới Tầm nhìn & Sứ mệnh (Khối 2).
    Admin có thể thêm, sửa, xóa, sắp xếp thứ tự và bật/tắt từng mục.
    """
    title = models.CharField(max_length=120, verbose_name="Tiêu đề")
    description = models.TextField(verbose_name="Mô tả")
    icon = models.CharField(
        max_length=80,
        blank=True,
        default="",
        verbose_name="Icon (emoji hoặc ký tự đặc biệt, VD: 🏛️)",
        help_text="Nhập emoji hoặc để trống nếu dùng ảnh minh họa.",
    )
    image = models.ImageField(
        upload_to="landing/grid/",
        null=True,
        blank=True,
        verbose_name="Ảnh minh họa (tùy chọn)",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Thứ tự hiển thị",
        help_text="Số nhỏ hơn hiển thị trước.",
    )
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Mục lưới trang giới thiệu"
        verbose_name_plural = "Lưới nội dung trang giới thiệu"

    def __str__(self) -> str:
        return self.title
