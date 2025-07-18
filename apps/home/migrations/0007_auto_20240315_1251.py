# Generated by Django 3.2.16 on 2024-03-15 12:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('home', '0006_auto_20240315_1241'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='customer',
            name='area_code',
            field=models.CharField(choices=[('+64', '+64 (New Zealand)'), ('+52', '+52 (Mexico)'), ('+34', '+34 (Spain)'), ('+44', '+44 (UK)'), ('+971', '+971 (UAE)'), ('+7', '+7 (Russia)'), ('+55', '+55 (Brazil)'), ('+61', '+61 (Australia)'), ('+91', '+91 (India)'), ('+81', '+81 (Japan)'), ('+39', '+39 (Italy)'), ('+65', '+65 (Singapore)'), ('+1', '+1 (Canada)'), ('+33', '+33 (France)'), ('+20', '+20 (Egypt)'), ('+49', '+49 (Germany)'), ('+82', '+82 (South Korea)'), ('+1', '+1 (US)'), ('+966', '+966 (Saudi Arabia)'), ('+86', '+86 (China)')], max_length=128),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('More than', 'More than'), ('More than and equals to', 'More than and equals to'), ('Equals to', 'Equals to'), ('Less than', 'Less than'), ('Less than and equals to', 'Less than and equals to'), (None, '-------')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('More than', 'More than'), ('More than and equals to', 'More than and equals to'), ('Equals to', 'Equals to'), ('Less than', 'Less than'), ('Less than and equals to', 'Less than and equals to'), (None, '-------')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='type',
            field=models.CharField(choices=[('Quotation', 'Quotation'), ('Purchase', 'Purchase')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='discount_type',
            field=models.CharField(choices=[('Fixed Amount', 'Fixed Amount'), ('Rate(%)', 'Rate(%)'), (None, '-------')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Valid', 'Valid'), ('Ready to start', 'Ready to start'), ('Paused', 'Paused'), ('Ended', 'Ended'), ('Cancelled', 'Cancelled')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Discount Voucher', 'Discount Voucher'), ('Manual Discount', 'Manual Discount'), ('Free Gift', 'Free Gift'), ('Product Combo', 'Product Combo')], max_length=128),
        ),
    ]
