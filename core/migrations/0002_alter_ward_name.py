# Generated by Django 5.1.4 on 2025-01-03 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ward',
            name='name',
            field=models.CharField(help_text='Name of the ward', max_length=100),
        ),
    ]
