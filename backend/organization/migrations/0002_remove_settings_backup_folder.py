from django.db import migrations


class Migration(migrations.Migration):
    """The backup folders moved to .env.use (DECISIONS.md D-019)."""

    dependencies = [
        ("organization", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="settings",
            name="backup_folder",
        ),
    ]
