from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AboutCoreValue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140, verbose_name="Tên cột")),
                ("description", models.TextField(verbose_name="Nội dung")),
                ("icon_class", models.CharField(blank=True, default="bi bi-building", max_length=80, verbose_name="Icon class (Bootstrap Icons)")),
                ("image", models.ImageField(blank=True, null=True, upload_to="about/core-values/", verbose_name="Ảnh minh họa (tùy chọn)")),
                ("display_order", models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")),
                ("is_active", models.BooleanField(default=True, verbose_name="Đang hiển thị")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Tầm nhìn & Sứ mệnh",
                "verbose_name_plural": "Tầm nhìn & Sứ mệnh",
                "ordering": ["display_order", "-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="AboutHeroSection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220, verbose_name="Tiêu đề chính")),
                ("welcome_text", models.TextField(verbose_name="Lời ngỏ")),
                ("background_image", models.ImageField(blank=True, null=True, upload_to="about/hero/", verbose_name="Ảnh nền Hero")),
                ("is_active", models.BooleanField(default=True, verbose_name="Đang sử dụng")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Banner & Lời ngỏ",
                "verbose_name_plural": "Banner & Lời ngỏ",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddField(
            model_name="aboutannouncement",
            name="summary",
            field=models.TextField(default="", verbose_name="Mô tả ngắn"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="aboutannouncement",
            name="thumbnail",
            field=models.ImageField(blank=True, null=True, upload_to="about/news/", verbose_name="Ảnh thu nhỏ"),
        ),
        migrations.AlterModelOptions(
            name="aboutannouncement",
            options={
                "ordering": ["-published_at", "-created_at"],
                "verbose_name": "Tin tức trang giới thiệu",
                "verbose_name_plural": "Tin tức trang giới thiệu",
            },
        ),
        migrations.AlterField(
            model_name="aboutannouncement",
            name="content",
            field=models.TextField(verbose_name="Nội dung chi tiết"),
        ),
    ]
