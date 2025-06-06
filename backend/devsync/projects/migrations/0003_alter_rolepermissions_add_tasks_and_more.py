# Generated by Django 5.1.7 on 2025-03-23 20:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_alter_rolepermissions_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rolepermissions',
            name='add_tasks',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='rolepermissions',
            name='add_tasks_in_department',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='rolepermissions',
            name='add_voting',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='rolepermissions',
            name='vote_in_voting',
            field=models.BooleanField(default=True),
        ),
    ]
