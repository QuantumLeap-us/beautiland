from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import datetime

from apps.home.model.commons import Commons
from apps.home.model.voucher import Voucher
from apps.home.models import Product, Customer
from apps.authentication.models import User


def get_file_path(instance, filename):
    # Upload path: user/<user_id>/image.jpg
    return f"media/payment_records/{instance.id}/{filename}"

class Orderitems(Commons):
    id=models.BigAutoField(primary_key=True)
    product = models.ForeignKey(Product, related_name='order_list', on_delete=models.SET_NULL, null=True)
    total_cost=models.FloatField(null=True)
    selling_price=models.FloatField(null=True)
    quantity = models.IntegerField(null=True)
    delivered_quantity = models.IntegerField(default=0)
    damage_quantity = models.IntegerField(null=True)
    remarks = models.CharField(max_length=128, null=True)    
    delivery_date = models.DateField(null=True, blank=True)
    delivery_status_option = models.options = (
        ('Pending', _('Pending')),
        ('Pending Delivery', _('Pending Delivery')),
        ('Partially Delivered', _('Partially Delivered')),
        ('Delivering', _('Delivering')),
        ('Delivered', _('Delivered')),
        ('Handling', _('Handling')),
        ('Completed', _('Completed')),
        ('Cancelled', _('Cancelled')),
        ('Out of Stock', _('Out of Stock')),
        ('Partial Out of Stock', _('Partial Out of Stock')),
    )
    delivery_status = models.CharField(max_length=128, null=True, choices=delivery_status_option, default='Pending')

    class Meta:
        db_table='orderitems'
        verbose_name = _('orderitem')
        verbose_name_plural = _('orderitems')

    def __int__(self) -> int:
        return self.id

class Order(Commons):
    id=models.BigAutoField(primary_key=True)
    order_id=models.CharField(max_length=18, null=True, unique=True)
    orderitems = models.ManyToManyField(Orderitems, related_name='order', )
    customer=models.ForeignKey(Customer, related_name='order', null=True, on_delete=models.CASCADE)
    delivery_cost=models.FloatField(default=0, null=True)
    delivery_date = models.DateField(null=True) 
    delivery_address = models.CharField(max_length=255)
    delivery_comment = models.CharField(max_length=255, blank=True, null=True)
    delivery_method_option = models.options = (
        ("self-pickup", _("Self-Pickup")),
        ("SF Express", _("SF Express")),
        ("salesperson delivery", _("salesperson delivery")),
        ("GOGOVAN", _("GOGOVAN"))
    )
    total_quantity = models.FloatField()
    delivery_method = models.CharField(max_length=50, choices=delivery_method_option, null=True)
    other_cost = models.FloatField(default=0, null=True)
    total_cost=models.FloatField(null=True)
    manual_cost=models.FloatField(null=True)
    voucher = models.ManyToManyField(Voucher, related_name='orders')
    payment_method = models.options =(
        ('COD',_('COD')),
        ('Bank Transfer', _('Bank Transfer')),
        ('Cheque', _('Cheque'))
    )
    payment_method = models.CharField(max_length=128, choices=payment_method, null=True)
    payment_date = models.DateTimeField(null=True)
    delivery_status_option = models.options = (
        ('Pending', _('Pending')),
        ('Pending Delivery', _('Pending Delivery')),
        ('Partially Delivered', _('Partially Delivered')),
        ('Delivering', _('Delivering')),
        ('Delivered', _('Delivered')),
        ('Handling', _('Handling')),
        ('Completed', _('Completed')),
        ('Cancelled', _('Cancelled')),
        ('Out of Stock', _('Out of Stock')),
        ('Partial Out of Stock', _('Partial Out of Stock')),
    )
    delivery_status = models.CharField(max_length=128, null=True, choices=delivery_status_option, default='Pending')
    free_gift = models.ManyToManyField(Product)
    payment_status_type = models.options = (
        ('Paid', _('paid')),
        ('Pending', _('Pending')),
        ('Failed', _('Failed'))
    )
    payment_status = models.CharField(max_length=50, null=True ,choices=payment_status_type, default='Pending')
    
    type_options = models.options = (
        ("Invoice", _("Invoice")),
        ("Quotation", _("Quotation"))
    )
    date=models.DateField(null=True)
    type = models.CharField(max_length=50, choices=type_options, default='Invoice')
    payment_record = models.FileField(upload_to=get_file_path, null=True)
    currency_options = models.options = (
        ('USD','USD'),
        ('CNY','CNY'),
        ('HKD','HKD')
    )
    currency = models.CharField(max_length=10, choices=currency_options, default='HKD')
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)
    old_order = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, help_text="Add order id when order is submitted for approval.")
    order_status = models.CharField(max_length=50, null=True, blank=True, default='pending payment')
    approval_comments = models.CharField(max_length=1024, null=True)
    can_change_sales_person = models.BooleanField(default=False)
    is_approve = models.BooleanField(default=True)
    order_type_options = models.options = (
        ('Sales Order', 'Sales Order'),
        ('Redlivery', 'Redlivery'),
        ('Redlivery - Broken', 'Redlivery - Broken'), 
        ('Redelivery & Return', 'Redelivery & Return'),
        ('Return', 'Return')
    )
    order_type = models.CharField(max_length=100, choices=order_type_options, default="Sales Order")
    warehouse_comment = models.TextField(null=True, blank=True)

    class Meta:
        db_table='order'
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __int__(self) -> int:
        return self.id
    
class Order_notification(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    approval_for = models.CharField(max_length=100)
    message = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    

class DeliverOrder(Commons):
    delivery_id = models.CharField(max_length=128, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    delivery_fee = models.FloatField(default=0)
    handle_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    delivery_comments = models.CharField(max_length=255, blank=True, null=True)
    delivery_method = models.CharField(max_length=255, blank=True, null=True)
    warehouse_comment = models.CharField(max_length=255, blank=True, null=True)
    delivery_address = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.DateField(null=True, blank=True)
    delivered_order_status_options = models.options = (
        ('Cancelled', 'Cancelled'),
    )
    delivered_order_status = models.CharField(max_length=128, null=True, blank=True, choices=delivered_order_status_options)
    cancel_delivery_reason = models.TextField(null=True, blank=True)
    self_deliver_order = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, help_text="Add deliver id when after sales is created for this deliver id.")

    
class DeliverOrderitems(Commons):
    deliver_order = models.ForeignKey(DeliverOrder, on_delete=models.CASCADE, null=True, blank=True)
    order_items = models.ForeignKey(Orderitems, on_delete=models.CASCADE)
    delivered_quantity = models.IntegerField(default=0)
    failed_delivery_quantity = models.IntegerField(default=0)
    redelivery_quantity = models.IntegerField(default=0)
    overdelivery_quantity = models.IntegerField(default=0)
    return_quantity = models.IntegerField(default=0)
    self_deliver_order_item = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, help_text="Add deliver order item id when after sales is created for this deliver order item.")

