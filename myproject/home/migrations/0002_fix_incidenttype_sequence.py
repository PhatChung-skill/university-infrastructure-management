from django.db import migrations


def fix_incidenttype_sequence(apps, schema_editor):
    """
    Đồng bộ lại sequence ID cho bảng home_incidenttype để tránh lỗi
    duplicate key khi thêm loại sự cố mới.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT setval(
              'home_incidenttype_id_seq',
              COALESCE((SELECT MAX(id) FROM home_incidenttype), 1),
              true
            );
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(fix_incidenttype_sequence, migrations.RunPython.noop),
    ]

