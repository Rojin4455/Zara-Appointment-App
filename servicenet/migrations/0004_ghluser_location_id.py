# Generated by Django 5.2 on 2025-06-09 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicenet', '0003_alter_ghluser_calendar_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='ghluser',
            name='location_id',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
    ]
