from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.home.models import Commons, Product
from apps.home.model.supplier import Supplier
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.authentication.models import User
from apps.home.model.order import Orderitems


class Inventory(Commons):
    id = models.BigAutoField(primary_key=True)
    product = models.OneToOneField(Product, null=False, on_delete=models.CASCADE)
    out_of_stock = models.BooleanField(default=False)
    current_quantity = models.IntegerField(default=0)
    # actual_quantity = models.IntegerField(default=0)
    # safety_quantity = models.IntegerField(default=0)
    # last_sales_date = models.DateField(null=True)
    # last_purchase_date = models.DateField(null=True)
    # total_stock_in_quantity=models.IntegerField(default=0)
    # total_stock_out_quantity=models.IntegerField(default=0)
    # total_damaged_quantity=models.IntegerField(default=0)
    # total_purchased_quantity=models.IntegerField(default=0)
    # total_sold_quantity=models.IntegerField(default=0)
    # total_shipping_quantity=models.IntegerField(default=0)

    class Meta:
        db_table = 'inventory'
        verbose_name = _('inventory')
        verbose_name_plural = _('inventory')

    def __int__(self):
        return self.id

    @receiver(post_save, sender=Product)
    def create_inventory_instance(sender, instance, created, **kwargs):
        if created:
            Inventory.objects.create(product=instance)
    
    # def save(self, *args, **kwargs):
    #     self.current_quantity = self.total_stock_in_quantity - self.total_stock_out_quantity - self.total_damaged_quantity 
    #     if self.current_quantity<=0:
    #         self.out_of_stock=True

    #     self.actual_quantity = self.current_quantity-self.total_sold_quantity

    #     return super(Inventory, self).save(*args, **kwargs)


class InventoryPurchaseOrderItems(Commons):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    item_name_chinese = models.CharField(max_length=200)
    item_name_english = models.CharField(max_length=200, null=True, blank=True)
    item_specification = models.CharField(max_length=100, null=True, blank=True)
    item_currency = models.CharField(max_length=100)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True)
    supplier_name = models.CharField(max_length=200)
    purchase_cost = models.FloatField()
    quantity = models.IntegerField()
    subtotal = models.FloatField()
    remark = models.CharField(max_length=500, null=True, blank=True)
    inventory_po_status = models.options = (
        ('Draft', _('draft')),
        ('Pending Stock In', _('pending stock in')),
        ('Cancelled', _('cancelled')),
        ('Stocked In', _('stocked in')),
    )
    status = models.CharField(choices=inventory_po_status, max_length=100)


class InventoryPurchaseOrder(Commons):
    inventory_po_id = models.CharField(max_length=500, null=True, blank=True, unique=True)
    inventory_purchase_items = models.ManyToManyField(InventoryPurchaseOrderItems)
    total_quantity = models.IntegerField(null=True, blank=True)
    total_purchase_cost = models.FloatField()
    special_disocunt = models.FloatField(null=True, blank=True)
    total_cost = models.FloatField()
    expected_arrival_date = models.DateField(null=True, blank=True)
    delivery_fee = models.FloatField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)


class StockInOrder(Commons):
    stockin_order_id = models.CharField(max_length=500, null=True, blank=True)
    inventory_po_item = models.ForeignKey(InventoryPurchaseOrderItems, on_delete=models.PROTECT, null=True, blank=True)
    depreciation = models.IntegerField(null=True, blank=True)
    actual_stock_in = models.IntegerField(null=True, blank=True)
    stock_in_remark = models.CharField(max_length=500, null=True, blank=True)
    staff = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)


class StockMove(Commons):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    move_type_choices = models.options = (
        ('Purchase', _('purchase')),
        ('Exchange', _('exchange')),
        ('Depreciation', _('depreciation')),
        ('Cycle Count', _('cycle count')),
        ('Sample', _('sample')),
        ('Others', _('others')),
    )
    move_type = models.CharField(choices=move_type_choices, max_length=100)
    remark = models.CharField(max_length=500, null=True, blank=True)
    quantity = models.IntegerField()
    stockin_order = models.ForeignKey(StockInOrder, null=True, blank=True, on_delete=models.PROTECT)
    

# class OrderDelivery(Commons):
#     delivery_id = models.CharField(max_length=500, null=True, blank=True)
#     order_item = models.ForeignKey(Orderitems, on_delete=models.CASCADE)
#     delivery_date = models.DateField(null=True, blank=True)
#     delivered_qty = models.IntegerField(default=0)
    
