# Generated by Django 5.2 on 2025-05-03 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0010_remove_role_permissions_rolepermission'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='permissions',
            field=models.ManyToManyField(blank=True, related_name='+', through='roles.RolePermission', to='roles.permission'),
        ),
    ]
