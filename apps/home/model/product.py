from apps.home.model.commons import Commons
from apps.home.model.product_category import Category
from django.db import models

from django.utils.translation import gettext_lazy as _
from apps.authentication.models import User
from apps.home.model.supplier import Supplier
import os


SHELF_LIFE_CHOICES = [
        ("years", "Years"),
        ("months", "Months"),
        ("days", "Days"),
    ]

def get_file_path(instance, filename):
    # Upload path: user/<user_id>/image.jpg
    return f"media/product/{instance.product.id}/{filename}"


class Product(Commons):
    id = models.BigAutoField(primary_key=True)
    brand = models.CharField(max_length=128, null=True, blank=True)
    category = models.ForeignKey(Category, related_name='main_category', on_delete=models.PROTECT)
    sub_category = models.ForeignKey(Category, related_name='sub_category', on_delete=models.PROTECT)
    product_id = models.CharField(max_length=500, null=True, blank=True, unique=True)
    barcode_no = models.CharField(max_length=500, null=True, blank=True)
    shelf_life_value = models.IntegerField(null=True, blank=True)
    shelf_life_time = models.CharField(max_length=50, choices=SHELF_LIFE_CHOICES, null=True, blank=True)
    product_chinese_name = models.CharField(max_length=128)
    product_english_name = models.CharField(max_length=128, null=True, blank=True)
    unit_of_measurement = models.CharField(max_length=128)
    unit_weight = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=128)
    out_of_stock = models.BooleanField(default=False)
    onboarding_date = models.DateField()
    sales_currency = models.CharField(max_length=128)
    retail_price = models.FloatField()
    selling_price = models.FloatField()
    bundle_product = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    bundle_product_price = models.FloatField(null=True, blank=True)
    cost_of_retail = models.FloatField()
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.PROTECT)
    supplier_product_name = models.CharField(max_length=128, null=True, blank=True)
    ingredient = models.TextField(null=True, blank=True) 
    product_remark = models.TextField(null=True, blank=True)
    raw_cost = models.FloatField(null=True, blank=True)
    packaging_cost = models.FloatField(null=True, blank=True)
    processing_cost = models.FloatField(null=True, blank=True)
    other_cost = models.FloatField(null=True, blank=True)
    delivery_fee_to_hk = models.FloatField(null=True, blank=True)
    currency_of_cost = models.CharField(max_length=128)
    total_cost = models.FloatField(null=True, blank=True)
    safe_number = models.IntegerField(null=True, blank=True)
    purchasing_amount = models.FloatField(null=True, blank=True)
    created_by=models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        db_table='product'
        verbose_name = _('product')
        verbose_name_plural = _('products')


    def __str__(self)->str:
        return f"{self.id}-{self.product_english_name}"
    
    # def save(self, *args, **kwargs):
    #     self.specifications = f"{self.unit_weight} {self.unit_weight_category}"
    #     return super(Product, self).save(*args, **kwargs)


class Product_Files(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_file_path, blank=True, null=True)
    file_name = models.CharField(max_length=500, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Retrieve old file path before saving the new file
        old_file = None
        if self.pk:
            old_file = Product_Files.objects.get(pk=self.pk).file

        # Call the superclass' save() method
        super().save(*args, **kwargs)

        # Delete the old file if it exists
        if old_file:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)


# class Product(Commons):
#     id = models.BigAutoField(primary_key=True)
#     category = models.ForeignKey(Category, null=True, related_name='main_category',on_delete=models.SET_NULL)
#     sub_category = models.ForeignKey(Category, null=True, related_name='sub_category',on_delete=models.SET_NULL)
#     product_id = models.CharField(max_length=128, unique=True, null=True)
#     barcode_no = models.CharField(max_length=128, null=True)
#     brand = models.CharField(max_length=128, null=False, blank=False)
#     specifications = models.CharField(max_length=128)
#     product_chinese_name = models.CharField(max_length=128, null=False, blank=False)
#     product_english_name = models.CharField(max_length=128, null=True)
#     supplier_product_name = models.CharField(max_length=128, null=True)
#     unit_of_measurement = models.CharField(max_length=128)
#     unit_weight_category = models.CharField(max_length=128, null=True)
#     unit_weight = models.FloatField()
#     status = models.CharField(max_length=128)
#     sales_currency = models.CharField(max_length=128)
#     retail_price = models.FloatField()
#     selling_price = models.FloatField()
#     std_cost_of_sales = models.FloatField()
#     shelf_date = models.DateField(null=True)
#     supplier = models.ForeignKey(Supplier, null=True, on_delete=models.SET_NULL)
#     ingredient_list = models.CharField(max_length=128,null=True) 
#     shelf_life = models.DateField(null=True)

#     class Meta:
#         db_table='product'
#         verbose_name = _('product')
#         verbose_name_plural = _('products')


#     def __str__(self)->str:
#         return f"{self.id}-{self.product_english_name}"
    
#     # def save(self, *args, **kwargs):
#     #     self.specifications = f"{self.unit_weight} {self.unit_weight_category}"
#     #     return super(Product, self).save(*args, **kwargs)
    