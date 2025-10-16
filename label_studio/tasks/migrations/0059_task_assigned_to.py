# RBAC-feature
# Generated manually for TICKET-006

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0058_task_precomputed_agreement"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="assigned_to",
            field=models.ManyToManyField(
                blank=True,
                help_text="Users assigned to this task",
                related_name="assigned_tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
