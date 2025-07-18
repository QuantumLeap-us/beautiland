# Generated by Django 3.2.16 on 2024-04-30 08:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('home', '0046_auto_20240430_0833'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), ('Equals to', 'Equals to'), ('More than', 'More than'), ('Less than', 'Less than'), (None, '-------')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), ('Equals to', 'Equals to'), ('More than', 'More than'), ('Less than', 'Less than'), (None, '-------')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Delivered', 'Delivered'), ('Partially Delivered', 'Partially Delivered'), ('Pending', 'Pending')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='type',
            field=models.CharField(choices=[('Purchase', 'Purchase'), ('Quotation', 'Quotation')], max_length=128),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='prefix',
            field=models.CharField(choices=[('+65', '+65 (Singapore)'), ('+7', '+7 (Russia)'), ('+33', '+33 (France)'), ('+39', '+39 (Italy)'), ('+1', '+1 (US)'), ('+971', '+971 (UAE)'), ('+64', '+64 (New Zealand)'), ('+86', '+86 (China)'), ('+81', '+81 (Japan)'), ('+61', '+61 (Australia)'), ('+55', '+55 (Brazil)'), ('+52', '+52 (Mexico)'), ('+91', '+91 (India)'), ('+966', '+966 (Saudi Arabia)'), ('+34', '+34 (Spain)'), ('+20', '+20 (Egypt)'), ('+44', '+44 (UK)'), ('+82', '+82 (South Korea)'), ('+49', '+49 (Germany)'), ('+1', '+1 (Canada)')], max_length=250),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='discount_type',
            field=models.CharField(choices=[('Fixed Amount', 'Fixed Amount'), ('Rate(%)', 'Rate(%)'), (None, '-------')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Ended', 'Ended'), ('Valid', 'Valid'), ('Cancelled', 'Cancelled'), ('Ready to start', 'Ready to start'), ('Paused', 'Paused')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Product Combo', 'Product Combo'), ('Manual Discount', 'Manual Discount'), ('Discount Voucher', 'Discount Voucher'), ('Free Gift', 'Free Gift')], max_length=128),
        ),
    ]
