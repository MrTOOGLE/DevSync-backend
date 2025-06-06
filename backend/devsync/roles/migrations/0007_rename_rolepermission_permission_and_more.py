# Generated by Django 5.2 on 2025-05-03 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0005_role_is_everyone'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='RolePermission',
            new_name='Permission',
        ),
        migrations.AlterField(
            model_name='role',
            name='permissions',
            field=models.ManyToManyField(blank=True, related_name='+', to='roles.permission'),
        ),
    ]
