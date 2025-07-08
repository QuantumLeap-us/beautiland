# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
# Create your models here.
from apps.home.model.commons import Commons
from apps.home.model.customer import Customer, Address
from apps.home.model.product import Product
from apps.home.model.product_picture import ProductPicture
from apps.home.model.product_category import Category
from apps.home.model.inventory import Inventory
from apps.home.model.purchase_details import Purchase, PurchaseItems
from apps.home.model.order import Order, Orderitems
from apps.home.model.voucher import * 
from apps.home.model.supplier import Supplier


class SystemParameters(Commons):
    system_parameter = models.CharField(max_length=150)
    name = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)


class SystemParametersForId(Commons):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    value = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)


class ExceptionLogs(Commons):
    error_type = models.CharField(max_length=500, null=True, blank=True)
    error_msg = models.TextField(null=True, blank=True)
    traceback = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
