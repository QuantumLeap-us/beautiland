# Generated by Django 3.2.16 on 2025-04-15 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0012_auto_20240726_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='permissions',
            name='role',
            field=models.CharField(choices=[('admin', 'admin'), ('staff', 'staff'), ('seller', 'seller')], default='seller', max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('admin', 'admin'), ('staff', 'staff'), ('seller', 'seller')], default='seller', max_length=128),
        ),
    ]
