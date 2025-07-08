from django.db import models
from apps.home.model.commons import Commons
from apps.home.models import Product

from django.utils.translation import gettext_lazy as _

PAYMENT_METHODS={
    ('COD','COD'),
    ('Bank Transfer/Cheque', 'Bank Transfer/Cheque')
}

DELIVEREY_STATUS={
    ('Pending', _('Pending')),
    ('Delivered', _('Delivered')),
    ('Partially Delivered', _('Partially Delivered')),
}

TYPEOFRECORD={
    ('Quotation', _('Quotation')),
    ('Purchase', _('Purchase')),
}

class PurchaseItems(Commons):
    id=models.BigAutoField(primary_key=True)
    product = models.ForeignKey(Product, related_name='purchase_list', on_delete=models.SET_NULL, null=True)
    raw_material_cost = models.FloatField(default=0, null=True)
    packaging_cost=models.FloatField(default=0, null=True)
    processing_cost=models.FloatField(default=0, null=True)
    product_other_cost=models.FloatField(default=0, null=True)
    freight_cost=models.FloatField(default=0, null=True)
    total_cost=models.FloatField(null=True)
    recommended_purchase_quantity = models.IntegerField(null=True)
    delivered_quantity = models.IntegerField(null=True)
    damage_quantity = models.IntegerField(null=True)

    class Meta:
        db_table='purchase_items'

    def __int__(self) -> int:
        return self.id
    
class Purchase(Commons):
    id=models.BigAutoField(primary_key=True)
    purchase_id = models.CharField(max_length=128, unique=True, null=True)
    purchase_items = models.ManyToManyField(PurchaseItems, related_name='purchases')
    delivery_date = models.DateField(null=True)
    delivery_cost = models.IntegerField(null=True)
    total_cost = models.IntegerField(null=True)
    total_product_cost = models.IntegerField(null=True)
    payment_method = models.CharField(max_length=128, choices=PAYMENT_METHODS, null=True)
    other_cost = models.IntegerField(null=True)
    actual_arrival_date = models.DateField(null=True)
    remarks = models.CharField(max_length=128, null=True)
    status = models.CharField(max_length=128, choices=DELIVEREY_STATUS, default='Pending')
    type = models.CharField(max_length=128, choices=TYPEOFRECORD)

    class Meta:
        db_table='purchase'

    def __int__(self) -> int:
        return self.id