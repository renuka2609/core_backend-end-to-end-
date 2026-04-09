from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0005_add_auditevent_indexes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='auditevent',
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['resource_type', 'resource_id', '-created_at'], name='audit_audit_resourc_b8e1d0_idx'),
                    models.Index(fields=['user', '-created_at'], name='audit_audit_user_id_605853_idx'),
                ],
            },
        ),
    ]
