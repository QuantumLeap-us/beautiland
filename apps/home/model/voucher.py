from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.home.model.commons import Commons

from apps.home.models import Product, Category, Customer
from apps.authentication.models import User

STATUS = {
    ('Ready to start',_('Ready to start')),
    ('Valid', _('Valid')),
    ('Paused', _('Paused')),
    ('Ended', _('Ended')),
    ('Cancelled', _('Cancelled'))
}

VOUCHER_TYPE = {
    ('Product Combo', _('Product Combo')),
    ('Discount Voucher', _('Discount Voucher')),
    ('Free Gift', _('Free Gift')),
    ('Manual Discount', _('Manual Discount')),
}

DISCOUNT_TYPE = {
    (None,'-------'),
    ('Fixed Amount',_('Fixed Amount')),
    ('Rate(%)',_('Rate(%)')),
}

TRIGGER_TYPE = {
    (None,'-------'),
    ('More than',_('More than')),
    ('More than and equals to',_('More than and equals to')),
    ('Equals to',_('Equals to')),
    ('Less than and equals to',_('Less than and equals to')),
    ('Less than',_('Less than')),

}

class ProductCombo(Commons):
    id = models.BigAutoField(primary_key=True)    
    product = models.ForeignKey(Product, related_name='product_combo', on_delete=models.CASCADE)
    min_quantity = models.FloatField()
    max_quantity = models.FloatField()

    class Meta:
        db_table='product_combo'

    def __str__(self)->str:
        return self.product.product_chinese_name
    
class DiscountVoucher(Commons):
    id = models.BigAutoField(primary_key=True)    
    only_available_to = models.ManyToManyField(Product)
    quantity = models.FloatField(null=True)
    price = models.FloatField(null=True)
    amount_trigger = models.CharField(max_length=128, choices=TRIGGER_TYPE, null=True)
    quantity_trigger = models.CharField(max_length=128, choices=TRIGGER_TYPE, null=True)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    no_of_gift = models.IntegerField(null=True)

    class Meta:
        db_table='discount_voucher'

    def __str__(self)->str:
        return self.id
    
# class ComboDetail(Commons):
#     id = models.BigAutoField(primary_key=True)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     productcombo = models.ForeignKey(ProductCombo, on_delete=models.CASCADE)


#     class Meta:
#         db_table='combo_detail'

#     def __str__(self)->str:
#         return self.productcombo.chinese_name


class Voucher(Commons):
    id = models.BigAutoField(primary_key=True)
    voucherid = models.CharField(max_length=128, unique=True, null=True)
    chinese_name = models.CharField(max_length=128)
    english_name = models.CharField(max_length=128)
    voucher_highlights = models.CharField(max_length=128, null=True)
    voucher_details = models.CharField(max_length=128, null=True)
    voucher_type = models.CharField(max_length=128, choices=VOUCHER_TYPE)
    discount_type = models.CharField(max_length=128, null=True ,choices=DISCOUNT_TYPE)
    discount_value = models.FloatField(null=True)
    product_combo = models.ForeignKey(ProductCombo, null=True, on_delete=models.SET_NULL)
    discount_voucher = models.ForeignKey(DiscountVoucher, null=True, on_delete=models.SET_NULL)
    quota = models.PositiveIntegerField(null=True)
    last_modified_date = models.DateTimeField(auto_now=True) 
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=128, choices=STATUS)
    created_by = models.ForeignKey(User, related_name='vouchers', on_delete=models.CASCADE)
    
    class Meta:
        db_table='voucher'

    def __str__(self)->str:
        return self.chinese_name
    

# class AvailableToProduct(Commons):
#     id = models.BigAutoField(primary_key=True)
#     voucher = models.ForeignKey(Voucher, related_name='applicable_products', on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     catgeory = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)

#     class Meta:
#         db_table='available_to_product'

#     def __str__(self)->str:
#         return f"{self.voucher} - {self.product}"
    
class VoucherUsage(Commons):
    id = models.BigAutoField(primary_key=True)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    
    class Meta:
        db_table='voucher_usage'

    def __str__(self) -> str:
        return f"{self.voucher.english_name}-{self.customer.company_english_name}"
