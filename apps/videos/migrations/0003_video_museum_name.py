# Generated by Django 5.2.3 on 2025-07-28 15:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("videos", "0002_remove_duration_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="museum_name",
            field=models.CharField(default="unknown", max_length=200),
        ),
    ]
