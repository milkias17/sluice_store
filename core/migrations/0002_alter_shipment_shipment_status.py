# Generated by Django 4.2.17 on 2025-01-01 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='shipment_status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered')], default='Pending', max_length=50),
        ),
    ]