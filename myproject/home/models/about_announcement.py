from django.db import models
from django.utils import timezone


class AboutHeroSection(models.Model):
    title = models.CharField(max_length=220, verbose_name="Tiêu đề chính")
    welcome_text = models.TextField(verbose_name="Lời ngỏ")
    background_image = models.ImageField(
        upload_to="about/hero/",
        null=True,
        blank=True,
        verbose_name="Ảnh nền Hero",
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang sử dụng")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Banner & Lời ngỏ"
        verbose_name_plural = "Banner & Lời ngỏ"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            AboutHeroSection.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)


class AboutCoreValue(models.Model):
    title = models.CharField(max_length=140, verbose_name="Tên cột")
    description = models.TextField(verbose_name="Nội dung")
    icon_class = models.CharField(
        max_length=80,
        blank=True,
        default="bi bi-building",
        verbose_name="Icon class (Bootstrap Icons)",
    )
    image = models.ImageField(
        upload_to="about/core-values/",
        null=True,
        blank=True,
        verbose_name="Ảnh minh họa (tùy chọn)",
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Đang hiển thị")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-updated_at"]
        verbose_name = "Tầm nhìn & Sứ mệnh"
        verbose_name_plural = "Tầm nhìn & Sứ mệnh"

    def __str__(self) -> str:
        return self.title


class AboutAnnouncement(models.Model):
    title = models.CharField(max_length=180, verbose_name="Tiêu đề")
    summary = models.TextField(default="", blank=True, verbose_name="Mô tả ngắn")
    content = models.TextField(verbose_name="Nội dung chi tiết")
    thumbnail = models.ImageField(
        upload_to="about/news/",
        null=True,
        blank=True,
        verbose_name="Ảnh thu nhỏ",
    )
    is_published = models.BooleanField(default=True, verbose_name="Đang hiển thị")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian đăng")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-published_at"]
        verbose_name = "Tin tức trang giới thiệu"
        verbose_name_plural = "Tin tức trang giới thiệu"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        if not self.is_published:
            self.published_at = None
        super().save(*args, **kwargs)


class AboutFeaturedEvent(models.Model):
    title = models.CharField(max_length=220, verbose_name="Tiêu đề sự kiện")
    summary = models.TextField(default="", blank=True, verbose_name="Mô tả ngắn")
    image = models.ImageField(
        upload_to="about/events/",
        null=True,
        blank=True,
        verbose_name="Ảnh sự kiện",
    )
    event_date = models.DateField(null=True, blank=True, verbose_name="Ngày sự kiện")
    is_published = models.BooleanField(default=True, verbose_name="Đang hiển thị")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian đăng")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-published_at", "-event_date"]
        verbose_name = "Sự kiện nổi bật"
        verbose_name_plural = "Sự kiện nổi bật"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        if not self.is_published:
            self.published_at = None
        super().save(*args, **kwargs)
