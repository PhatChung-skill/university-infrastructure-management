from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0004_alter_aboutannouncement_summary"),
    ]

    operations = [
        migrations.CreateModel(
            name="AboutFeaturedEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220, verbose_name="Tiêu đề sự kiện")),
                ("summary", models.TextField(blank=True, default="", verbose_name="Mô tả ngắn")),
                ("image", models.ImageField(blank=True, null=True, upload_to="about/events/", verbose_name="Ảnh sự kiện")),
                ("event_date", models.DateField(blank=True, null=True, verbose_name="Ngày sự kiện")),
                ("is_published", models.BooleanField(default=True, verbose_name="Đang hiển thị")),
                ("published_at", models.DateTimeField(blank=True, null=True, verbose_name="Thời gian đăng")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Sự kiện nổi bật",
                "verbose_name_plural": "Sự kiện nổi bật",
                "ordering": ["-event_date", "-published_at", "-created_at"],
            },
        ),
    ]
