from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0003_seed_about_page_content"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aboutannouncement",
            name="summary",
            field=models.TextField(blank=True, default="", verbose_name="Mô tả ngắn"),
        ),
    ]
