from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inspection', '0023_automationrule_target_situation_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='inspectiontype',
            name='vehicle_types',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
