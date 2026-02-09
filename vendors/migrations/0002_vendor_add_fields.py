# Generated migration for adding vendor fields

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='industry',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='vendor',
            name='tier',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='vendor',
            name='status',
            field=models.CharField(default='active', max_length=32),
        ),
    ]
