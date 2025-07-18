# Generated by Django 3.2.16 on 2024-07-24 12:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0062_auto_20240711_1752'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stockinorder',
            name='inventory_po',
        ),
        migrations.AddField(
            model_name='stockinorder',
            name='inventory_po_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='home.inventorypurchaseorderitems'),
        ),
        migrations.AddField(
            model_name='stockinorder',
            name='stock_move',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='home.stockmove'),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('More than', 'More than'), (None, '-------'), ('Less than', 'Less than'), ('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), ('Equals to', 'Equals to')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('More than', 'More than'), (None, '-------'), ('Less than', 'Less than'), ('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), ('Equals to', 'Equals to')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Partially Delivered', 'Partially Delivered'), ('Pending', 'Pending'), ('Delivered', 'Delivered')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='stockmove',
            name='move_type',
            field=models.CharField(choices=[('Purchase', 'purchase'), ('Exchange', 'exchange'), ('Depreciation', 'depreciation'), ('Cycle Count', 'cycle count'), ('Sample', 'sample'), ('Others', 'others')], max_length=100),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='prefix',
            field=models.CharField(choices=[('+81', '+81 (Japan)'), ('+86', '+86 (China)'), ('+52', '+52 (Mexico)'), ('+82', '+82 (South Korea)'), ('+966', '+966 (Saudi Arabia)'), ('+20', '+20 (Egypt)'), ('+64', '+64 (New Zealand)'), ('+61', '+61 (Australia)'), ('+971', '+971 (UAE)'), ('+7', '+7 (Russia)'), ('+39', '+39 (Italy)'), ('+34', '+34 (Spain)'), ('+1', '+1 (US)'), ('+91', '+91 (India)'), ('+65', '+65 (Singapore)'), ('+44', '+44 (UK)'), ('+49', '+49 (Germany)'), ('+55', '+55 (Brazil)'), ('+33', '+33 (France)'), ('+1', '+1 (Canada)')], max_length=250),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='discount_type',
            field=models.CharField(choices=[('Fixed Amount', 'Fixed Amount'), (None, '-------'), ('Rate(%)', 'Rate(%)')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Ready to start', 'Ready to start'), ('Valid', 'Valid'), ('Cancelled', 'Cancelled'), ('Ended', 'Ended'), ('Paused', 'Paused')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Discount Voucher', 'Discount Voucher'), ('Free Gift', 'Free Gift'), ('Manual Discount', 'Manual Discount'), ('Product Combo', 'Product Combo')], max_length=128),
        ),
    ]
