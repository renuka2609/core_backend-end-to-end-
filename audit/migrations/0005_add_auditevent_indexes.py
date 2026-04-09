from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0004_auditevent_add_org_and_rename_fields'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['resource_type', 'resource_id', '-created_at'], name='audit_audit_resourc_b8e1d0_idx'),
        ),
        migrations.AddIndex(
            model_name='auditevent',
            index=models.Index(fields=['user', '-created_at'], name='audit_audit_user_id_605853_idx'),
        ),
    ]
