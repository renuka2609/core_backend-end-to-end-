from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0002_vendor_add_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='accounts.tenant',
            ),
        ),
        migrations.AddField(
            model_name='vendor',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vendor',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='vendor',
            name='org',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='vendors',
                to='orgs.organization',
            ),
        ),
        migrations.AlterModelOptions(
            name='vendor',
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['org', '-created_at'], name='vendors_ven_org_id_28e7b9_idx'),
                ],
            },
        ),
    ]
