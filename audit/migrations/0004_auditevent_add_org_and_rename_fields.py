# Generated manually to align AuditEvent model with current field names and add org tenant isolation

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0003_remove_auditevent_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='auditevent',
            name='org',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='orgs.organization',
                help_text='Organization that owns this audit event',
            ),
        ),
        migrations.RenameField(
            model_name='auditevent',
            old_name='entity_type',
            new_name='resource_type',
        ),
        migrations.RenameField(
            model_name='auditevent',
            old_name='entity_id',
            new_name='resource_id',
        ),
        migrations.RenameField(
            model_name='auditevent',
            old_name='description',
            new_name='metadata',
        ),
        migrations.AlterField(
            model_name='auditevent',
            name='action',
            field=models.CharField(
                max_length=255,
                help_text="Action performed (e.g., 'assessment_transitioned: assigned → submitted')",
            ),
        ),
        migrations.AlterField(
            model_name='auditevent',
            name='resource_type',
            field=models.CharField(
                max_length=50,
                null=True,
                blank=True,
                help_text="Type of resource affected (e.g., 'assessment', 'review', 'vendor')",
            ),
        ),
        migrations.AlterField(
            model_name='auditevent',
            name='resource_id',
            field=models.IntegerField(
                null=True,
                blank=True,
                help_text="ID of resource affected",
            ),
        ),
        migrations.AlterField(
            model_name='auditevent',
            name='metadata',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Additional context: old_value, new_value, actor details, request metadata',
            ),
        ),
        migrations.AlterField(
            model_name='auditevent',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                help_text='User who performed the action',
            ),
        ),
    ]
