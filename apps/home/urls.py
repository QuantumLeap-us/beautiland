# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views

urlpatterns = [

    # 前台展示页面 - 无需登录
    path('frontend/', views.frontend_home, name='frontend_home'),
    path('frontend/products/', views.frontend_products, name='frontend_products'),

    # The home page (后台管理)
    path('', views.index, name='home'),
    path('category-list/', views.categoryList, name="category-list"),
    path('category/', views.categoryCreate, name="category"),
    path('category-delete/<int:id>/', views.categoryDelete, name="category-delete"),

    path('inventory-list/',views.inventoryList, name="inventory-list"),
    path('inventory-purchase-order/', views.inventory_purchase_order, name="inventory_purchase_order"),
    path('create-inventory-purchase-order/', views.create_inventory_purchase_order, name="create_inventory_purchase_order"),
    path('inventory-purchase-order-list/', views.inventory_purchase_order_list, name="inventory_purchase_order_list"),
    path('inventory-purchase-order-details/<int:inv_po_id>/', views.inventory_purchase_order_details, name="inventory_purchase_order_details"),
    path('update-inventory-purchase-order/', views.update_inventory_purchase_order, name="update_inventory_purchase_order"),
    path('inventory-list-export/', views.inventory_list_export, name="inventory_list_export"),
    path('inventory_stockin_list/', views.inventory_stockin_list, name="inventory_stockin_list"),
    path('inventory_stockin_list_export/', views.inventory_stockin_list_export, name="inventory_stockin_list_export"),
    path('inventory_stockin_order/', views.inventory_stockin_order, name="inventory_stockin_order"),
    path('create_inventory_stockin/', views.create_inventory_stockin, name="create_inventory_stockin"),
    path('inventory_edit_stockin_order/<int:id>/', views.inventory_edit_stockin_order, name="inventory_edit_stockin_order"),
    path('get_product/<str:product_id>/', views.get_product, name="get_product"),

    path('delivery-list/', views.delivery_list, name="delivery-list"),
    path('delivery_list_export/', views.delivery_list_export, name="delivery_list_export"),
    path('delivery_list_export_breakdown/', views.delivery_list_export_breakdown, name="delivery_list_export_breakdown"),
    path('delivery_details/<int:id>/', views.delivery_details, name="delivery_details"),
    path('save_item_delivery/', views.save_item_delivery, name="save_item_delivery"),
    path('generate_pdf_for_delivery_note/<int:order_id>/<int:deliver_id>/', views.generate_pdf_for_delivery_note, name="generate_pdf_for_delivery_note"),
    path('after_sales_generate_pdf_for_delivery_note/<int:order_id>/<int:deliver_id>/', views.after_sales_generate_pdf_for_delivery_note, name="after_sales_generate_pdf_for_delivery_note"),
    path('cancel_delivered_order/', views.cancel_delivered_order, name="cancel_delivered_order"),
    path('after_sales_delivery/<int:id>/', views.after_sales_delivery, name="after_sales_delivery"),
    path('save_after_sales_delivery/', views.save_after_sales_delivery, name="save_after_sales_delivery"),

    path('product-list/', views.productList, name="product-list"),
    path('product/', views.productCreate, name="product"),
    path('product-update/<int:id>/', views.productUpdate, name="product-update"),
    path('product-details/<int:id>/', views.productGet, name="product-details"),
    path('product-delete/<int:id>/', views.productDelete, name="product-delete"),
    path('product-export/', views.product_list_export, name="product-export"),
    path('product-import/', views.importfromcsv, name="product-import"),
    path('get_supplier/', views.get_supplier, name="get_supplier"),
    path('get_bundle_product/', views.get_bundle_product, name="get_bundle_product"),
    path('product_delete/', views.product_delete, name="product_delete"),
    path('remove_product_image/', views.remove_product_image, name="remove_product_image"),
    path('download_product_image/<int:id>/', views.download_product_image, name="download_product_image"),
    path('get_coc_converted_price/', views.get_coc_converted_price, name="get_coc_converted_price"),
    path('products_import/', views.products_import, name="products_import"),
    path('product_import_samplefile/', views.product_import_samplefile, name="product_import_samplefile"),

    path('customer-list/', views.customerList, name="customer-list"),
    path('customer_list_export/', views.customer_list_export, name="customer_list_export"),
    path('customer/', views.customerCreate, name="customer"),
    path('customer-update/<int:id>/', views.customerUpdate, name="customer-update"),
    path('customer-details/<int:id>/', views.customerGet, name="customer-details"),
    path('customer-delete/<int:id>/', views.customerDelete, name="customer-delete"),
    path('customer_delete/', views.customer_delete, name="customer_delete"),
    path('download_customer_name_card/<int:id>/', views.download_customer_name_card, name="download_customer_name_card"),
    path('remove_customer_name_card/', views.remove_customer_name_card, name="remove_customer_name_card"),
    path('customer_import_samplefile/', views.customer_import_samplefile, name="customer_import_samplefile"),
    path('customers_import/', views.customers_import, name="customers_import"),

    path('purchase/', views.purchaseCreate, name="purchase"),
    path('purchase-list/', views.purchaseList, name="purchase-list"),
    path('purchase-get/<int:id>/', views.purchaseGet, name="purchase-get"),
    path('purchase-delete/<int:id>/', views.PurchaseDelete, name="purchase-delete"),

    path('order/', views.OrderNewcreate, name="order"),
    # path('place-order/', views.placeOrder, name="place-order"),
    path('order-list/', views.orderList, name="order-list"),
    path('order-update/', views.order_update, name="order-update"),
    path('order-resubmit/', views.resubmit_order, name="order-resubmit"),
    path('cancel-order/<int:id>', views.cancel_order, name="cancel-order"),
    path('order-confirmation/<int:id>/', views.confirmOrderDelivery, name="order-confirmation"),
    path('order-get/<int:id>/', views.orderGet, name="order-get"),
    path('order-delete/<int:id>/', views.OrderDelete, name="order-delete"),
    path('search_customer/', views.SearchCustomer.as_view(),name="search-customer" ),
    path('download-payment-record/<int:id>', views.download_payment_record,name="download-payment-record" ),
    path('order-list-export/', views.order_list_export, name="order-list-export" ),
    path('order_import_samplefile/', views.order_import_samplefile, name="order_import_samplefile"),
    path('order_import/', views.order_import, name="order_import"),
    path('get_currency_converted_price/', views.get_currency_converted_price, name="get_currency_converted_price"),
    path('get_notification/', views.get_notification, name="get_notification"),
    path('approve_request/', views.approve_request, name="approve_request"),
    path('reject_request/', views.reject_request, name="reject_request"),
    path('get_notification_count/', views.get_notification_count, name="get_notification_count"),
    path('order_submit/', views.order_submit, name="order_submit"),
    path('generate-pdf/', views.generate_pdf, name='generate_pdf'),
    # path('get_vouchers/', views.get_vouchers,name="get_vouchers" ),

    path('voucher/', views.addVoucher, name="voucher"),
    path('voucher-list/', views.voucherList, name="voucher-list"),
    path('voucher-delete/<int:id>/', views.voucherDelete, name="voucher-delete"),
    path('voucher-details/<int:id>/', views.voucherGet, name="voucher-details"),

    path('supplier-list/', views.supplierList, name="supplier-list"),
    path('supplier-list-export/', views.supplier_list_export, name="supplier-list-export"),
    path('supplier/', views.SupplierCreate, name="supplier"),
    path('supplier-update/<int:id>/', views.supplierUpdate, name="supplier-update"),
    path('supplier-details/<int:id>/', views.supplierGet, name="supplier-details"),
    path('supplier-delete/<int:id>/', views.supplierDelete, name="supplier-delete"),
    path('supplier_delete/', views.supplier_delete, name="supplier_delete"),
    path('download_name_card/<int:id>/', views.download_name_card, name="download_name_card"),
    path('supplier_import_samplefile/', views.supplier_import_samplefile, name="supplier_import_samplefile"),
    path('suppliers_import/', views.suppliers_import, name="suppliers_import"),
    path('remove_supplier_name_card/', views.remove_supplier_name_card, name="remove_supplier_name_card"),

    path('quotation/', views.quotationCreate, name="quotation"),
    path('quotation-list/', views.quotationList, name="quotation-list"),
    path('quotation-get/<int:id>/', views.quotationGet, name="quotation-get"),
    path('quotation-update/<int:id>/', views.quotationUpdate, name="quotation-update"),
    path('quotation-pdf/<int:id>/', views.quotationPdf, name="quotation-pdf"),
    path('create-purchase/<int:id>/', views.quotationToPurchase, name="create-purchase"),

    path('in-stock-list/', views.InstockList, name="in-stock-list"),
    path('in-stock-details/<int:id>/', views.InstockGet, name="in-stock-get"),
    path('in-stock-delete/<int:id>/', views.InstockDelete, name="in-stock-delete"),
    path('in-stock-delivery/<int:id>/', views.InStockDelivery, name="in-stock-delivery"),

    path('address/<int:id>/', views.addressCreate, name="address"),
    path('address-update/<int:id>/', views.addressUpdate, name="address-update"),
    path('address-delete/<int:id>/', views.addressDelete, name="address-delete"),

    path('order-approval-list/', views.order_approval_list, name="order-approval-list"),
    path('order-approval-get/<int:id>/', views.order_approval_get, name="order-approval-get"),
    path('pending-order-approve/<int:id>/', views.pending_order_approve, name="pending-order-approve"),
    path('pending-order-reject/<int:id>/', views.pending_order_reject, name="pending-order-reject"),

    path('system_parameters_list/', views.system_parameters_list, name="system_parameters_list"),
    path('system_parameter/<int:id>/', views.system_parameter, name="system_parameter"),
    path('system_parameter_delete/<int:id>/', views.system_parameter_delete, name="system_parameter_delete"),

    path('transactions/create/', views.transaction_create, name='transaction-create'),
    path('transactions/update/<int:transaction_id>/', views.transaction_update, name='transaction-update'),
    path('transactions/detail/<int:transaction_id>/', views.transaction_detail, name='transaction-detail'),
    path('transactions/', views.transaction_list, name='transaction-list'),
    path('transactions/delete/<int:transaction_id>/', views.transaction_delete, name='transaction-delete'),
    path('transactions/import/', views.transaction_import, name='transaction-import'),
    path('transactions/approve/<int:transaction_id>/', views.transaction_approve, name='transaction-approve'),
    path('transactions/create-dynamic/', views.create_dynamic_transaction, name='transaction-create-dynamic'),
    path('transactions/transaction_create_with_redirect/', views.transaction_create_with_redirect,
         name='transaction_create_with_redirect'),

    path('schemes/', views.discount_scheme_list, name='discount_scheme_list'),
    path('schemes/create/', views.discount_scheme_create, name='discount_scheme_create'),
    path('schemes/edit/<int:pk>/', views.discount_scheme_edit, name='discount_scheme_edit'),
    path('schemes/delete/<int:pk>/', views.discount_scheme_delete, name='discount_scheme_delete'),
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/create/', views.coupon_create, name='coupon_create'),
    path('coupons/edit/<int:pk>/', views.coupon_edit, name='coupon_edit'),
    path('coupons/delete/<int:pk>/', views.coupon_delete, name='coupon_delete'),
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/create/', views.promotion_create, name='promotion_create'),
    path('promotions/edit/<int:pk>/', views.promotion_edit, name='promotion_edit'),
    path('promotions/delete/<int:pk>/', views.promotion_delete, name='promotion_delete'),
    path('promo_codes/', views.promo_code_list, name='promo_code_list'),
    path('promo_codes/create/', views.promo_code_create, name='promo_code_create'),
    path('promo_codes/edit/<int:pk>/', views.promo_code_edit, name='promo_code_edit'),
    path('promo_codes/delete/<int:pk>/', views.promo_code_delete, name='promo_code_delete'),
]