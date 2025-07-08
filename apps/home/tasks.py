# from celery import shared_task
# import pandas as pd
# from apps.home.models import Product, Category, Inventory
# from django.db import transaction



# @shared_task
# def process_csv_file(file):
#     try:
#         df = pd.read_excel(file)
#         product_to_insert = []
#         with transaction.atomic():
#             for _, row in df.iterrows():
#                 category, created = Category.objects.aget_or_create(name=row['Main Category'])
#                 sub_category, created = Category.objects.aget_or_create(name=row['Sub Category'])
#                 print(type(row['English Name']))

#                 if str(row['English Name'])=='nan':
#                     row['English Name']=None

#                 model_instance = Product(
#                     category=category,
#                     sub_category=sub_category,
#                     product_id=row['Product No'],
#                     brand=row['Brand Category'],
#                     product_chinese_name=row['Name'],
#                     product_english_name=row['English Name'],
#                     supplier_product_name=row['Supplier Product Name'],
#                     unit_of_measurement=row['Unit Of Measurement'],
#                     unit_weight_category=row['Unit Weight Category'],
#                     unit_weight=row['Unit Weight'],
#                     status=row['Status'],
#                     sales_currency=row['Sales Currency'],
#                     retail_price=row['Retail Price'],
#                     selling_price=row['Recommended Selling Price'],
#                     std_cost_of_sales=row['Cost of Sales'],
#                     supplier_no=row['Supplier Code'],
#                     supplier_name=row['Supplier'],
#                     shelf_life=row['Shelf life '],
#                     raw_material_cost=row['Raw Material Cost'],
#                     packging_cost=row['Packaging Cost'],
#                     processing_cost=row['Processing Cost'],
#                     other_cost=row['Other Cost'],
#                     freight_cost=row['Frieght Cost'],
#                     cost_currency=row['Cost Currency'],
#                     total_cost=row['Total Cost'],
#                     recommended_purchase_quantity=row['Recommeded purchase quantity']
#                 )
#                 product_to_insert.append(model_instance)
#             products = Product.objects.abulk_create(product_to_insert)
#             inventory_to_create = []
#             for product in products:
#                 inventory_to_create.append(Inventory(product=product))
#             invetories = Inventory.objects.abulk_create(inventory_to_create)
#     except Exception as e:
#         return str(e)