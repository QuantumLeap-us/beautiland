# Generated by Django 3.2.16 on 2024-03-06 12:56

import apps.home.model.order
import apps.home.model.product_picture
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('type', models.CharField(max_length=50, null=True)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='home.category')),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
                'db_table': 'category',
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('english_name', models.CharField(max_length=128, null=True)),
                ('company_name', models.CharField(max_length=128)),
                ('company_english_name', models.CharField(max_length=128, null=True)),
                ('contact_1', models.CharField(max_length=128, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only Numbers are allowed.')])),
                ('contact_2', models.CharField(max_length=128, null=True, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only Numbers are allowed.')])),
                ('area_code', models.CharField(choices=[('+49', '+49 (Germany)'), ('+966', '+966 (Saudi Arabia)'), ('+61', '+61 (Australia)'), ('+82', '+82 (South Korea)'), ('+971', '+971 (UAE)'), ('+64', '+64 (New Zealand)'), ('+1', '+1 (US)'), ('+34', '+34 (Spain)'), ('+20', '+20 (Egypt)'), ('+33', '+33 (France)'), ('+86', '+86 (China)'), ('+55', '+55 (Brazil)'), ('+39', '+39 (Italy)'), ('+91', '+91 (India)'), ('+81', '+81 (Japan)'), ('+7', '+7 (Russia)'), ('+52', '+52 (Mexico)'), ('+65', '+65 (Singapore)'), ('+1', '+1 (Canada)'), ('+44', '+44 (UK)')], max_length=128)),
                ('phone_number', models.CharField(max_length=128, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only Numbers are allowed.')])),
                ('phone_number_2', models.CharField(max_length=128, null=True, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only Numbers are allowed.')])),
                ('email', models.EmailField(max_length=254, null=True)),
                ('url', models.CharField(max_length=128, null=True)),
                ('landline', models.CharField(max_length=128, null=True, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only Numbers are allowed.')])),
                ('industry_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.category')),
                ('sale_person', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'customer',
                'verbose_name_plural': 'customers',
                'db_table': 'customer',
            },
        ),
        migrations.CreateModel(
            name='DiscountVoucher',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('quantity', models.FloatField(null=True)),
                ('price', models.FloatField(null=True)),
                ('amount_trigger', models.CharField(choices=[('Equals to', 'Equals to'), ('Less than', 'Less than'), ('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), ('More than', 'More than'), (None, '-------')], max_length=128, null=True)),
                ('quantity_trigger', models.CharField(choices=[('Equals to', 'Equals to'), ('Less than', 'Less than'), ('More than and equals to', 'More than and equals to'), ('Less than and equals to', 'Less than and equals to'), ('More than', 'More than'), (None, '-------')], max_length=128, null=True)),
                ('no_of_gift', models.IntegerField(null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.category')),
            ],
            options={
                'db_table': 'discount_voucher',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('product_id', models.CharField(max_length=128, null=True, unique=True)),
                ('barcode_no', models.CharField(max_length=128, null=True)),
                ('brand', models.CharField(max_length=128)),
                ('specifications', models.CharField(max_length=128)),
                ('product_chinese_name', models.CharField(max_length=128)),
                ('product_english_name', models.CharField(max_length=128, null=True)),
                ('supplier_product_name', models.CharField(max_length=128, null=True)),
                ('unit_of_measurement', models.CharField(max_length=128)),
                ('unit_weight_category', models.CharField(max_length=128, null=True)),
                ('unit_weight', models.FloatField()),
                ('status', models.CharField(max_length=128)),
                ('sales_currency', models.CharField(max_length=128)),
                ('retail_price', models.FloatField()),
                ('selling_price', models.FloatField()),
                ('std_cost_of_sales', models.FloatField()),
                ('shelf_date', models.DateField(null=True)),
                ('ingredient_list', models.CharField(max_length=128, null=True)),
                ('shelf_life', models.DateField(null=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='main_category', to='home.category')),
                ('sub_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sub_category', to='home.category')),
            ],
            options={
                'verbose_name': 'product',
                'verbose_name_plural': 'products',
                'db_table': 'product',
            },
        ),
        migrations.CreateModel(
            name='ProductCombo',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('min_quantity', models.FloatField()),
                ('max_quantity', models.FloatField()),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_combo', to='home.product')),
            ],
            options={
                'db_table': 'product_combo',
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=128)),
                ('name', models.CharField(max_length=128)),
                ('english_name', models.CharField(max_length=128, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('phone_number', models.CharField(max_length=128, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'Only Numbers are allowed.')])),
                ('address_line1', models.CharField(max_length=128, null=True)),
                ('address_line2', models.CharField(max_length=128, null=True)),
                ('pincode', models.PositiveIntegerField()),
                ('landmark', models.CharField(max_length=128, null=True)),
                ('town', models.CharField(max_length=128)),
                ('city', models.CharField(max_length=128)),
                ('state', models.CharField(max_length=128)),
                ('country', models.CharField(max_length=128)),
            ],
            options={
                'db_table': 'supplier',
            },
        ),
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('voucherid', models.CharField(max_length=128, null=True, unique=True)),
                ('chinese_name', models.CharField(max_length=128)),
                ('english_name', models.CharField(max_length=128)),
                ('voucher_highlights', models.CharField(max_length=128, null=True)),
                ('voucher_details', models.CharField(max_length=128, null=True)),
                ('voucher_type', models.CharField(choices=[('Product Combo', 'Product Combo'), ('Free Gift', 'Free Gift'), ('Manual Discount', 'Manual Discount'), ('Discount Voucher', 'Discount Voucher')], max_length=128)),
                ('discount_type', models.CharField(choices=[('Fixed Amount', 'Fixed Amount'), ('Rate(%)', 'Rate(%)'), (None, '-------')], max_length=128, null=True)),
                ('discount_value', models.FloatField(null=True)),
                ('quota', models.PositiveIntegerField(null=True)),
                ('last_modified_date', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True)),
                ('status', models.CharField(choices=[('Ended', 'Ended'), ('Valid', 'Valid'), ('Cancelled', 'Cancelled'), ('Paused', 'Paused'), ('Ready to start', 'Ready to start')], max_length=128)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vouchers', to=settings.AUTH_USER_MODEL)),
                ('discount_voucher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.discountvoucher')),
                ('product_combo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.productcombo')),
            ],
            options={
                'db_table': 'voucher',
            },
        ),
        migrations.CreateModel(
            name='VoucherUsage',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.customer')),
                ('voucher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.voucher')),
            ],
            options={
                'db_table': 'voucher_usage',
            },
        ),
        migrations.CreateModel(
            name='PurchaseItems',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('raw_material_cost', models.FloatField(default=0, null=True)),
                ('packaging_cost', models.FloatField(default=0, null=True)),
                ('processing_cost', models.FloatField(default=0, null=True)),
                ('product_other_cost', models.FloatField(default=0, null=True)),
                ('freight_cost', models.FloatField(default=0, null=True)),
                ('total_cost', models.FloatField(null=True)),
                ('recommended_purchase_quantity', models.IntegerField(null=True)),
                ('delivered_quantity', models.IntegerField(null=True)),
                ('damage_quantity', models.IntegerField(null=True)),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchase_list', to='home.product')),
            ],
            options={
                'db_table': 'purchase_items',
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('purchase_id', models.CharField(max_length=128, null=True, unique=True)),
                ('delivery_date', models.DateField(null=True)),
                ('delivery_cost', models.IntegerField(null=True)),
                ('total_cost', models.IntegerField(null=True)),
                ('total_product_cost', models.IntegerField(null=True)),
                ('payment_method', models.CharField(choices=[('Bank Transfer/Cheque', 'Bank Transfer/Cheque'), ('COD', 'COD')], max_length=128, null=True)),
                ('other_cost', models.IntegerField(null=True)),
                ('actual_arrival_date', models.DateField(null=True)),
                ('remarks', models.CharField(max_length=128, null=True)),
                ('status', models.CharField(choices=[('Delivered', 'Delivered'), ('Partially Delivered', 'Partially Delivered'), ('Pending', 'Pending')], default='Pending', max_length=128)),
                ('type', models.CharField(choices=[('Quotation', 'Quotation'), ('Purchase', 'Purchase')], max_length=128)),
                ('purchase_items', models.ManyToManyField(related_name='purchases', to='home.PurchaseItems')),
            ],
            options={
                'db_table': 'purchase',
            },
        ),
        migrations.CreateModel(
            name='ProductPicture',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('image_name', models.CharField(max_length=128)),
                ('image', models.ImageField(upload_to=apps.home.model.product_picture.product_image_path)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.product')),
            ],
            options={
                'verbose_name': 'product picture',
                'verbose_name_plural': 'product pictures',
                'db_table': 'product_picture',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.supplier'),
        ),
        migrations.CreateModel(
            name='Orderitems',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('total_cost', models.FloatField(null=True)),
                ('selling_price', models.FloatField(null=True)),
                ('quantity', models.IntegerField(null=True)),
                ('delivered_quantity', models.IntegerField(null=True)),
                ('damage_quantity', models.IntegerField(null=True)),
                ('remarks', models.CharField(max_length=128, null=True)),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_list', to='home.product')),
            ],
            options={
                'verbose_name': 'orderitem',
                'verbose_name_plural': 'orderitems',
                'db_table': 'orderitems',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('delivery_cost', models.FloatField(default=0, null=True)),
                ('delivery_date', models.DateField()),
                ('delivery_address', models.CharField(max_length=255)),
                ('delivery_comment', models.CharField(max_length=255)),
                ('total_quantity', models.FloatField()),
                ('delivery_method', models.CharField(choices=[('self-pickup', 'Self-Pickup'), ('SF Express', 'SF Express'), ('salesperson delivery', 'salesperson delievery'), ('GOGOVAN', 'GOGOVAN')], max_length=50, null=True)),
                ('other_cost', models.FloatField(default=0, null=True)),
                ('total_cost', models.FloatField(null=True)),
                ('payment_method', models.CharField(choices=[('COD', 'COD'), ('Bank Transfer/Cheque', 'Bank Transfer/Cheque')], max_length=128)),
                ('payment_date', models.DateTimeField(null=True)),
                ('delievery_status', models.CharField(choices=[('Pending', 'Pending'), ('Partially Delievered', 'Partially Delievered'), ('Delievered', 'Delievered')], default='Pending', max_length=128)),
                ('status', models.CharField(max_length=128)),
                ('payment_status', models.CharField(choices=[('paid', 'paid'), ('pending', 'Pending'), ('fail', 'Fail')], max_length=50)),
                ('payment_record', models.FileField(null=True, upload_to=apps.home.model.order.get_file_path)),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order', to='home.customer')),
                ('free_gift', models.ManyToManyField(to='home.Product')),
                ('orderitems', models.ManyToManyField(related_name='order', to='home.Orderitems')),
                ('voucher', models.ManyToManyField(related_name='orders', to='home.Voucher')),
            ],
            options={
                'verbose_name': 'order',
                'verbose_name_plural': 'orders',
                'db_table': 'order',
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('out_of_stock', models.BooleanField(default=False)),
                ('current_quantity', models.IntegerField(default=0)),
                ('actual_quantity', models.IntegerField(default=0)),
                ('safety_quantity', models.IntegerField(default=0)),
                ('last_sales_date', models.DateField(null=True)),
                ('last_purchase_date', models.DateField(null=True)),
                ('total_stock_in_quantity', models.IntegerField(default=0)),
                ('total_stock_out_quantity', models.IntegerField(default=0)),
                ('total_damaged_quantity', models.IntegerField(default=0)),
                ('total_purchased_quantity', models.IntegerField(default=0)),
                ('total_sold_quantity', models.IntegerField(default=0)),
                ('total_shipping_quantity', models.IntegerField(default=0)),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='home.product')),
            ],
            options={
                'verbose_name': 'inventory',
                'verbose_name_plural': 'inventory',
                'db_table': 'inventory',
            },
        ),
        migrations.AddField(
            model_name='discountvoucher',
            name='only_available_to',
            field=models.ManyToManyField(to='home.Product'),
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('address_line1', models.CharField(max_length=128)),
                ('address_line2', models.CharField(max_length=128, null=True)),
                ('pincode', models.PositiveIntegerField()),
                ('landmark', models.CharField(max_length=128, null=True)),
                ('town', models.CharField(max_length=128)),
                ('city', models.CharField(max_length=128)),
                ('state', models.CharField(max_length=128)),
                ('country', models.CharField(max_length=128)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='home.customer')),
            ],
            options={
                'verbose_name': 'address',
                'verbose_name_plural': 'addresses',
                'db_table': 'address',
            },
        ),
    ]
