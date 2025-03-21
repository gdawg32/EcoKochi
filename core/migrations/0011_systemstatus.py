# Generated by Django 5.1.4 on 2025-01-25 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_complaint_feedback_notification_payment'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_status', models.CharField(choices=[('OPERATIONAL', 'System Fully Operational'), ('MAINTENANCE', 'Under Maintenance'), ('DEGRADED', 'Partially Operational'), ('DOWN', 'System Down')], default='OPERATIONAL', max_length=20)),
                ('message', models.TextField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('scheduled_maintenance', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'System Status',
            },
        ),
    ]
