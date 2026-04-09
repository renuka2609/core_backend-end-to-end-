from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0006_assessment_risk_level_assessment_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='status',
            field=models.CharField(
                choices=[
                    ('assigned', 'Assigned'),
                    ('submitted', 'Submitted'),
                    ('reviewed', 'Reviewed'),
                    ('approved', 'Approved'),
                    ('remediation', 'Remediation'),
                ],
                default='assigned',
                max_length=20,
            ),
        ),
    ]
