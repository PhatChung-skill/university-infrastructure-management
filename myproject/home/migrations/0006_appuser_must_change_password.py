from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_about_featured_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='must_change_password',
            field=models.BooleanField(default=False),
        ),
    ]
