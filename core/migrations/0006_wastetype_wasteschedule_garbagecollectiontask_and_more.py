# Generated by Django 5.1.4 on 2025-01-15 15:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_resident'),
    ]

    operations = [
        migrations.CreateModel(
            name='WasteType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the waste type (e.g., Organic, Plastic).', max_length=50, unique=True)),
                ('description', models.TextField(help_text='Description of the waste type (e.g., compostable materials).')),
                ('recycling_guidelines', models.TextField(blank=True, help_text='Guidelines for recycling this waste type.', null=True)),
                ('active', models.BooleanField(default=True, help_text='Is this waste type active for use?')),
            ],
        ),
        migrations.CreateModel(
            name='WasteSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collection_day', models.CharField(choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')], help_text='Day of the week for collection.', max_length=10)),
                ('start_time', models.TimeField(help_text='Start time for waste collection.')),
                ('end_time', models.TimeField(help_text='End time for waste collection.')),
                ('active', models.BooleanField(default=True, help_text='Is this schedule active?')),
                ('ward', models.ForeignKey(help_text='Ward associated with the schedule.', on_delete=django.db.models.deletion.CASCADE, related_name='waste_schedules', to='core.ward')),
                ('waste_type', models.ForeignKey(help_text='Type of waste to be collected.', on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='core.wastetype')),
            ],
        ),
        migrations.CreateModel(
            name='GarbageCollectionTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Assigned', 'Assigned'), ('In Progress', 'In Progress'), ('Completed', 'Completed')], default='Assigned', help_text='Status of the collection task.', max_length=15)),
                ('assigned_at', models.DateTimeField(auto_now_add=True, help_text='Time when the task was assigned.')),
                ('completed_at', models.DateTimeField(blank=True, help_text='Time when the task was completed.', null=True)),
                ('notes', models.TextField(blank=True, help_text='Additional information about the task.', null=True)),
                ('waste_collector', models.ForeignKey(help_text='Waste collector assigned to the task.', on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='core.wastecollector')),
                ('schedule', models.ForeignKey(help_text='Waste collection schedule.', on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='core.wasteschedule')),
            ],
        ),
        migrations.CreateModel(
            name='WasteReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(help_text='Details about the waste issue.')),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Resolved', 'Resolved')], default='Pending', help_text='Status of the waste report.', max_length=15)),
                ('reported_at', models.DateTimeField(auto_now_add=True, help_text='Time when the issue was reported.')),
                ('resolved_at', models.DateTimeField(blank=True, help_text='Time when the issue was resolved.', null=True)),
                ('resident', models.ForeignKey(help_text='Resident reporting the issue.', on_delete=django.db.models.deletion.CASCADE, related_name='waste_reports', to='core.resident')),
                ('waste_type', models.ForeignKey(help_text='Type of waste involved.', on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='core.wastetype')),
            ],
        ),
    ]
