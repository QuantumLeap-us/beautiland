# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from apps.home.models import Customer, Product, Category, Inventory, ExceptionLogs


class ExceptionLogsAdmin(admin.ModelAdmin):
    list_display  = ("error_type", "error_msg", "traceback")

# Register your models here.
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(ExceptionLogs, ExceptionLogsAdmin)