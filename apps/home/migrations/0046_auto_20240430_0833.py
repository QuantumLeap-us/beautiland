# Generated by Django 3.2.16 on 2024-04-30 08:33

import apps.home.model.product
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0045_auto_20240429_1030'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='std_cost_of_sales',
            new_name='cost_of_retail',
        ),
        migrations.RemoveField(
            model_name='product',
            name='ingredient_list',
        ),
        migrations.RemoveField(
            model_name='product',
            name='product_id',
        ),
        migrations.RemoveField(
            model_name='product',
            name='shelf_date',
        ),
        migrations.RemoveField(
            model_name='product',
            name='shelf_life',
        ),
        migrations.RemoveField(
            model_name='product',
            name='specifications',
        ),
        migrations.RemoveField(
            model_name='product',
            name='unit_weight_category',
        ),
        migrations.AddField(
            model_name='product',
            name='bundle_product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='home.product'),
        ),
        migrations.AddField(
            model_name='product',
            name='bundle_product_price',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='currency_of_cost',
            field=models.CharField(default='HKD', max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='delivery_fee_to_hk',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='ingredient',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='onboarding_date',
            field=models.DateField(default='2024-04-30'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='other_cost',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='out_of_stock',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='packaging_cost',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='processing_cost',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='product_id',
            field=models.CharField(blank=True, max_length=500, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='product_remark',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='purchasing_amount',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='raw_cost',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='safe_number',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='shelf_life_time',
            field=models.CharField(blank=True, choices=[('years', 'Years'), ('months', 'Months'), ('days', 'Days')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='shelf_life_value',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='amount_trigger',
            field=models.CharField(choices=[('More than and equals to', 'More than and equals to'), (None, '-------'), ('Less than and equals to', 'Less than and equals to'), ('Less than', 'Less than'), ('Equals to', 'Equals to'), ('More than', 'More than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='discountvoucher',
            name='quantity_trigger',
            field=models.CharField(choices=[('More than and equals to', 'More than and equals to'), (None, '-------'), ('Less than and equals to', 'Less than and equals to'), ('Less than', 'Less than'), ('Equals to', 'Equals to'), ('More than', 'More than')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='barcode_no',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(default=14, on_delete=django.db.models.deletion.PROTECT, related_name='main_category', to='home.category'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='product_english_name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='sub_category',
            field=models.ForeignKey(default=45, on_delete=django.db.models.deletion.PROTECT, related_name='sub_category', to='home.category'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(default=65, on_delete=django.db.models.deletion.PROTECT, to='home.supplier'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='supplier_product_name',
            field=models.CharField(default='test', max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='purchase',
            name='payment_method',
            field=models.CharField(choices=[('COD', 'COD'), ('Bank Transfer/Cheque', 'Bank Transfer/Cheque')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='status',
            field=models.CharField(choices=[('Partially Delivered', 'Partially Delivered'), ('Delivered', 'Delivered'), ('Pending', 'Pending')], default='Pending', max_length=128),
        ),
        migrations.AlterField(
            model_name='supplier',
            name='prefix',
            field=models.CharField(choices=[('+39', '+39 (Italy)'), ('+65', '+65 (Singapore)'), ('+966', '+966 (Saudi Arabia)'), ('+33', '+33 (France)'), ('+81', '+81 (Japan)'), ('+61', '+61 (Australia)'), ('+82', '+82 (South Korea)'), ('+86', '+86 (China)'), ('+20', '+20 (Egypt)'), ('+44', '+44 (UK)'), ('+1', '+1 (US)'), ('+55', '+55 (Brazil)'), ('+1', '+1 (Canada)'), ('+91', '+91 (India)'), ('+49', '+49 (Germany)'), ('+52', '+52 (Mexico)'), ('+64', '+64 (New Zealand)'), ('+971', '+971 (UAE)'), ('+7', '+7 (Russia)'), ('+34', '+34 (Spain)')], max_length=250),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='discount_type',
            field=models.CharField(choices=[('Fixed Amount', 'Fixed Amount'), (None, '-------'), ('Rate(%)', 'Rate(%)')], max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='status',
            field=models.CharField(choices=[('Ready to start', 'Ready to start'), ('Valid', 'Valid'), ('Paused', 'Paused'), ('Ended', 'Ended'), ('Cancelled', 'Cancelled')], max_length=128),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='voucher_type',
            field=models.CharField(choices=[('Discount Voucher', 'Discount Voucher'), ('Manual Discount', 'Manual Discount'), ('Free Gift', 'Free Gift'), ('Product Combo', 'Product Combo')], max_length=128),
        ),
        migrations.CreateModel(
            name='Product_Files',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, null=True, upload_to=apps.home.model.product.get_file_path)),
                ('file_name', models.CharField(blank=True, max_length=500, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.product')),
            ],
        ),
    ]
