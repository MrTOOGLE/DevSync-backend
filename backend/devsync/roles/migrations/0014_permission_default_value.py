# Generated by Django 5.2 on 2025-05-03 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0013_alter_role_date_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='permission',
            name='default_value',
            field=models.BooleanField(default=False),
        ),
    ]
