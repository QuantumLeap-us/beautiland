from datetime import datetime, timedelta
from PIL import Image
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django.db import transaction
import pandas as pd
import os, json, sys
from pathlib import Path
from apps.home.forms.productform import ProductForm
from apps.home.forms.productimportform import importForm
from apps.home.model.product_category import Category
from apps.home.models import Inventory, Product, Supplier, Order
from apps.home.model.product import Product_Files
from django.contrib.auth.decorators import login_required
# from apps.home.tasks import process_csv_file
from apps.home.models import SystemParameters, SystemParametersForId
from apps.authentication.models import User
from celery.result import AsyncResult
from django.utils.translation import gettext_lazy as _
from apps.home.crud import utils, storage_backends, manager
import base64, traceback
from django.utils.safestring import mark_safe
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import CharField
from django.db.models.functions import Lower
from django.conf import settings
from apps.home.model.inventory import InventoryPurchaseOrderItems, StockMove, Orderitems
from django.db.models import Sum
 

@login_required(login_url="/login/")
def productList(request):
    form = ProductForm()
    # products = Inventory.objects.select_related('product').all()        
    products_data = []
    try:
        products = Product.objects.values(
            "id",
            "brand",
            "category_id",
            "category__name",
            "sub_category_id",
            "sub_category__name",
            "product_id",
            "barcode_no",
            "shelf_life_value",
            "shelf_life_time",
            "product_chinese_name",
            "product_english_name",
            "unit_of_measurement",
            "unit_weight",
            "status",
            "out_of_stock",
            "onboarding_date",
            "sales_currency",
            "retail_price",
            "selling_price",
            "bundle_product",
            "bundle_product_price",
            "cost_of_retail",
            "supplier_id",
            "supplier__company_name",
            "supplier__supplier_id",
            "supplier_product_name",
            "ingredient",
            "product_remark",
            "raw_cost",
            "packaging_cost",
            "processing_cost",
            "other_cost",
            "delivery_fee_to_hk",
            "currency_of_cost",
            "safe_number",
            "purchasing_amount",
            "created_by",
            "created_date",
            "total_cost",
        ).order_by("-id")

        product_ids = list(products.values_list("id", flat=True))
        product_wise_file = {}
        product_files = Product_Files.objects.filter(product_id__in=product_ids).values("product_id", "file", "file_name")
        for prod_file in product_files:
            if prod_file["product_id"] not in product_wise_file:
                product_wise_file[prod_file["product_id"]] = {"file_path": prod_file["file"], "file_name": prod_file["file_name"]}

        for product in products:
            base64_with_prefix = ""
            if product["id"] in product_wise_file:
                file_path = str(product_wise_file[product["id"]]["file_path"])
                bucket_name = settings.MEDIA_BUCKET_NAME
                file_name = str(product_wise_file[product["id"]]["file_name"])
                product_id = product["id"]
                object_name = f"{product_id}/{file_name}"
                base64_with_prefix = storage_backends.get_file(bucket_name, object_name)
                # if os.path.exists(file_path):
                #     with open(file_path, "rb") as file:
                #         image_data = file.read()
                #         base64_str = base64.b64encode(image_data).decode("utf-8")
                #         base64_with_prefix = "data:image/jpeg;base64," + base64_str 

            products_data.append({
                "id": product["id"],
                "created_date": datetime.strptime(str(product["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if product["created_date"] else "-",
                "product_id": product["product_id"],
                'product_chinese_name': product["product_chinese_name"],
                'product_english_name': product["product_english_name"] if product["product_english_name"] else "-",
                "category": product["category__name"],
                "sub_category": product["sub_category__name"] if product["sub_category__name"] else "-",
                "specification": str(product["unit_weight"]) + str(product["unit_of_measurement"]) if product["unit_weight"] and product["unit_of_measurement"] else "-",
                "retail_price": round(product["retail_price"], 2),
                "selling_price": round(product["selling_price"], 2),
                "cost_of_retail": round(product["cost_of_retail"], 2),
                "supplier__company_name": product["supplier__company_name"] if product["supplier__company_name"] else "-",
                "supplier_id": product["supplier__supplier_id"] if product["supplier__supplier_id"] else "-",
                "status": product["status"],
                "total_cost": product["total_cost"] if product["total_cost"] else "-",
                "currency_of_cost": product["currency_of_cost"] if product["currency_of_cost"] else "-",
                "name_card_file_name": product_wise_file[product["id"]]["file_name"] if product["id"] in product_wise_file else "-",
                "name_card_file_path": base64_with_prefix,
            })

        return render(request, 'home/product-list.html', {"products": products_data, 'form': form, "role": request.user.role})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/product-list.html', {"products": products_data, 'form': form, "role": request.user.role, "error_msg": str(e)})


@login_required(login_url="/login/")
def product_list_export(request):
    form = ProductForm()
    products_data = []
    try:
        products = Product.objects.values(
            "id",
            "brand",
            "category_id",
            "category__name",
            "sub_category_id",
            "sub_category__name",
            "product_id",
            "barcode_no",
            "shelf_life_value",
            "shelf_life_time",
            "product_chinese_name",
            "product_english_name",
            "unit_of_measurement",
            "unit_weight",
            "status",
            "out_of_stock",
            "onboarding_date",
            "sales_currency",
            "retail_price",
            "selling_price",
            "bundle_product",
            "bundle_product_price",
            "cost_of_retail",
            "supplier_id",
            "supplier__company_name",
            "supplier__supplier_id",
            "supplier_product_name",
            "ingredient",
            "product_remark",
            "raw_cost",
            "packaging_cost",
            "processing_cost",
            "other_cost",
            "delivery_fee_to_hk",
            "currency_of_cost",
            "safe_number",
            "purchasing_amount",
            "created_by",
            "created_date",
            "total_cost",
        ).order_by("-id")

        product_ids = list(products.values_list("id", flat=True))
        product_wise_file = {}
        product_files = Product_Files.objects.filter(product_id__in=product_ids).values("product_id", "file", "file_name")
        for prod_file in product_files:
            if prod_file["product_id"] not in product_wise_file:
                product_wise_file[prod_file["product_id"]] = {"file_path": prod_file["file"], "file_name": prod_file["file_name"]}

        for product in products:
            products_data.append({
                "Created Date": datetime.strptime(str(product["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if product["created_date"] else "",
                "Product ID": product["product_id"],
                'Product Chinese Name': product["product_chinese_name"],
                'Product English Name': product["product_english_name"] if product["product_english_name"] else "",
                "Category": product["category__name"],
                "Sub Category": product["sub_category__name"] if product["sub_category__name"] else "",
                "Specification": str(product["unit_weight"]) + str(product["unit_of_measurement"]) if product["unit_weight"] and product["unit_of_measurement"] else "",
                "Retail Price": round(product["retail_price"], 2),
                "Selling Price": round(product["selling_price"], 2),
                "Cost of Retail": round(product["cost_of_retail"], 2),
                "Total Stock Out": "",
                "Total Shipment Quantity": "",
                "Current Inventory": "",
                "Total Order Quantity": "",
                "Last Purchase Date": "",
                "Supplier": product["supplier__company_name"],
                "Supplier ID": product["supplier__supplier_id"],
                "Status": product["status"],
                "Actual Cost": product["total_cost"] if product["total_cost"] else "",
                "Currency of Cost": product["currency_of_cost"] if product["currency_of_cost"] else "",
                "Inventory After Sales": "",
                "Last Order Date": "",
                "Product Image": product_wise_file[product["id"]]["file_name"] if product["id"] in product_wise_file else "",
            })

        df = pd.DataFrame(products_data)

        now = datetime.now().strftime("%d%m%Y")
        file_path = 'media/temp/products/' + str(request.user.id) + "/"
        file_name = "products_" + str(now) + ".xlsx"
        full_file_path = file_path + file_name
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        df.to_excel(full_file_path, index=False)        

        response = FileResponse(open(full_file_path, 'rb'), content_type='text/xlsx')
        response['Content-Disposition'] = f'attachment; filename=' + file_name
        return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/product-list.html', {"products": products_data, 'form': form, "role": request.user.role, "error_msg": str(e)})


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def products_import(request):
    try:
        if request.method == "POST":
            import_product_file = request.FILES.get("import_product_file")
            if import_product_file:
                with transaction.atomic():
                    xlsx_df = pd.read_excel(import_product_file)
                    xlsx_df = xlsx_df.map(lambda x: None if pd.isna(x) or x == '' else x)
                    products_dict = xlsx_df.to_dict(orient='records')
                    mandatory_field = []
                    wrong_data_fields = []
                    missing_categories = []
                    missing_prod_id_pattern_categories = []

                    exist_products = []
                    for product in products_dict:
                        brand = product["Brand"] if "Brand" in product and product["Brand"] else None
                        category = product["Category"] if "Category" in product and product["Category"] else None
                        sub_category = product["Sub Category"] if "Sub Category" in product and product["Sub Category"] else None
                        barcode = product["Barcode"] if "Barcode" in product and product["Barcode"] else None
                        shelf_life = product["Shelf Life"] if "Shelf Life" in product and product["Shelf Life"] else None
                        product_chinese_name = product["Product Chinese Name"] if "Product Chinese Name" in product and product["Product Chinese Name"] else None
                        product_english_name = product["Product English Name"] if "Product English Name" in product and product["Product English Name"] else None
                        unit_of_measurement = product["Unit of Measurement"] if "Unit of Measurement" in product and product["Unit of Measurement"] else None
                        weight = product["Weight"] if "Weight" in product and product["Weight"] else None
                        onboarding_date = datetime.strptime(str(product["Onboarding Date"]), "%Y-%m-%d %H:%M:%S").date() if "Onboarding Date" in product and product["Onboarding Date"] else datetime.now().date()
                        currency = product["Currency"] if "Currency" in product and product["Currency"] else None
                        retail_price = product["Retail Price"] if "Retail Price" in product and product["Retail Price"] else None
                        selling_price = product["Selling Price"] if "Selling Price" in product and product["Selling Price"] else None
                        cost_of_retail = product["Cost of Retail"] if "Cost of Retail" in product and product["Cost of Retail"] else None
                        ingredient = product["Ingredient"] if "Ingredient" in product and product["Ingredient"] else None
                        product_remark = product["Product Remark"] if "Product Remark" in product and product["Product Remark"] else None
                        raw_cost = product["Raw Cost"] if "Raw Cost" in product and product["Raw Cost"] else 0
                        packaging_cost = product["Packaging Cost"] if "Packaging Cost" in product and product["Packaging Cost"] else 0
                        processing_cost = product["Processing Cost"] if "Processing Cost" in product and product["Processing Cost"] else 0
                        other_cost = product["Other Cost"] if "Other Cost" in product and product["Other Cost"] else 0
                        delivery_fee_to_hk = str(product["Delivery Fee to HK"]) if "Delivery Fee to HK" in product and product["Delivery Fee to HK"] else 0
                        currency_of_cost = product["Currency of Cost"] if "Currency of Cost" in product and product["Currency of Cost"] else None
                        safe_number = product["Safe Number"] if "Safe Number" in product and product["Safe Number"] else None
                        purchasing_amount = product["Purchasing Amount"] if "Purchasing Amount" in product and product["Purchasing Amount"] else None

                        total_cost = int(raw_cost) + int(packaging_cost) + int(processing_cost) + int(other_cost) + int(delivery_fee_to_hk)

                        shelf_life_value = ""
                        shelf_life_time = ""
                        if shelf_life:
                            shelf_life_li = shelf_life.split()
                            if len(shelf_life_li) > 1:
                                shelf_life_value = shelf_life_li[0]
                                shelf_life_time = shelf_life_li[1]
                            else:
                                if "Shelf Life" not in wrong_data_fields:
                                    wrong_data_fields.apend("Shelf Life")

                        if not category and "Category" not in mandatory_field:
                            mandatory_field.append("Category")
                        if not sub_category and "Sub Category" not in mandatory_field:
                            mandatory_field.append("Sub Category")
                        if not product_chinese_name and "Product Chinese Name" not in mandatory_field:
                            mandatory_field.append("Product Chinese Name")
                        if not unit_of_measurement and "Unit of Measurement" not in mandatory_field:
                            mandatory_field.append("Unit of Measurement")
                        if not currency and "Currency" not in mandatory_field:
                            mandatory_field.append("Currency")
                        if not retail_price and "Retail Price" not in mandatory_field:
                            mandatory_field.append("Retail Price")
                        if not selling_price and "Selling Price" not in mandatory_field:
                            mandatory_field.append("Selling Price")
                        if not cost_of_retail and "Cost of Retail" not in mandatory_field:
                            mandatory_field.append("Cost of Retail")
                        if not currency_of_cost and "Currency of Cost" not in mandatory_field:
                            mandatory_field.append("Currency of Cost")

                        if mandatory_field:
                            break

                        exist_product = Product.objects.filter(
                            category__name=category,
                            sub_category__name=sub_category,
                            product_chinese_name=product_chinese_name,
                            unit_of_measurement=unit_of_measurement,
                            sales_currency=currency,
                            currency_of_cost=currency_of_cost,
                            ).first()

                        if exist_product:
                            exist_products.append(product_chinese_name)
                            continue

                        sys_params = SystemParameters.objects.filter(system_parameter__in=["Brand", "Unit of Measurement", "Currency", "Currency of Cost"])
                        for sys_param in sys_params:
                            if brand and sys_param.system_parameter == "Brand" and brand.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + brand.capitalize()
                            if unit_of_measurement and sys_param.system_parameter == "Unit of Measurement" and unit_of_measurement.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + unit_of_measurement.capitalize()
                            if currency and sys_param.system_parameter == "Currency" and currency.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + currency.upper()
                            if currency_of_cost and sys_param.system_parameter == "Currency of Cost" and currency_of_cost.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + currency_of_cost.upper()
                            sys_param.save()

                        exist_category = Category.objects.filter(type="Product Category", name=category, parent__isnull=True).first()
                        exist_subcategory = Category.objects.filter(type="Product Category", name=sub_category, parent__name=category).first()
                        if not exist_category and not exist_subcategory:
                            missing_categories.append("category `<b>" + category + "</b>` - sub category `<b>" + sub_category + "</b>`")
                        elif exist_category and not exist_subcategory:
                            missing_categories.append("sub category `<b>" + sub_category + "</b>`")
                        elif not exist_category and exist_subcategory:
                            missing_categories.append("category `<b>" + category + "</b>`")

                        if missing_categories:    
                            continue
                        
                        prod_id_pattern = ""
                        if category:
                            prod_id_pattern = SystemParametersForId.objects.filter(category__name=category).values("value").first()
                            if not prod_id_pattern or not prod_id_pattern["value"]:
                                missing_prod_id_pattern_categories.append(category)
                                continue

                        current_date = datetime.now().date()
                        if onboarding_date > current_date:
                            status = "in preparation"
                        else:
                            status = "in sales"

                        product_obj = Product.objects.create(
                            brand=brand,
                            category_id=exist_category.id,
                            sub_category_id=exist_subcategory.id,
                            barcode_no=barcode,
                            shelf_life_value=shelf_life_value,
                            shelf_life_time=shelf_life_time,
                            product_chinese_name=product_chinese_name,
                            product_english_name=product_english_name,
                            unit_of_measurement=unit_of_measurement,
                            unit_weight=weight,
                            status=status,
                            onboarding_date=onboarding_date,
                            sales_currency=currency,
                            retail_price=retail_price,
                            selling_price=selling_price,
                            cost_of_retail=cost_of_retail,
                            ingredient=ingredient,
                            product_remark=product_remark,
                            raw_cost=raw_cost,
                            packaging_cost=packaging_cost,
                            processing_cost=processing_cost,
                            other_cost=other_cost,
                            delivery_fee_to_hk=delivery_fee_to_hk,
                            currency_of_cost=currency_of_cost,
                            total_cost=total_cost,
                            safe_number=safe_number,
                            purchasing_amount=purchasing_amount,
                            created_by=request.user,
                        )

                        if product_obj:
                            latest_product = Product.objects.filter(product_id__icontains=prod_id_pattern["value"]).values("product_id").order_by("-id").first()
                            latest_pro_id = 1
                            if latest_product:
                                latest_pro_id = int(latest_product["product_id"].replace(prod_id_pattern["value"], "")) + 1
                            product_obj.product_id = prod_id_pattern["value"] + str(latest_pro_id)
                            # product_obj.product_id = prod_id_pattern["value"] + str(product_obj.id)
                            product_obj.save()

                    if mandatory_field:
                        msg = "`<b>" + ", ".join(mandatory_field) + "</b>` fields are mandatory. <div style='padding-top: 7px !important;'>Please add relevant data!</div>" if len(mandatory_field) > 1 else "`<b>" + ", ".join(mandatory_field) + "</b>` field is mandatory. <div style='padding-top: 7px !important;'>Please add relevant data!</div>"
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")

                    if wrong_data_fields:
                        msg = "Please add relevant data for fields `<b>" + ", ".join(wrong_data_fields) + "</b>`." if len(wrong_data_fields) > 1 else "Please add relevant data for field `<b>" + ", ".join(wrong_data_fields) + "</b>`."
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")

                    if missing_categories:
                        msg = "Please add " + ", ".join(missing_categories) + " in the system parameters."
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")

                    if missing_prod_id_pattern_categories:
                        msg = "Please add Product ID pattern for categories `<b>" + ", ".join(missing_prod_id_pattern_categories) + "</b>` in the system parameters." if len(exist_products) > 1 else "Please add Product ID pattern for category `<b>" + ", ".join(missing_prod_id_pattern_categories) + "</b>` in the system parameters."
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")

                    if exist_products:
                        msg = "`<b>" + ", ".join(exist_products) + "</b>` products are already exist." if len(exist_products) > 1 else "`<b>" + ", ".join(exist_products) + "</b>` product is already exist."
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")

                return HttpResponse(json.dumps({"code": 1, "msg": "Success."}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@login_required(login_url="/login/")
def product_import_samplefile(request):
    try:
        full_file_path = 'sample_files/import_products_sample_file.xlsx'
        response = utils.download_samplefile(full_file_path, "import_products_sample_file.xlsx")
        if response:
            return response
        return render(request, 'home/product-list.html', {"error_msg": "Sample file not found."})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/product-list.html', {"error_msg": str(e)})


# @login_required(login_url="/login/")
# def inventoryList(request):

#     products = Inventory.objects.select_related('product').all()

#     return render(request, 'home/inventory-list.html', {"products": products})


# @login_required(login_url="/login/")
# def productCreate(request):
#     msg = ''
#     form = ProductForm(request.POST, request.FILES)
#     if request.method == "POST":

#         if form.is_valid():

#             try:
#                 with transaction.atomic():
#                     obj = form.save(commit=False)
#                     obj.specifications = f"{form.cleaned_data['unit_weight']} {form.cleaned_data['unit_weight_category']}"

#                     if obj.status == "On Sale":
#                         obj.shelf_date = datetime.now().date()
  
#                     obj.save()
#                     obj.product_id=str(obj.brand[0:2]) + str('{:07d}'.format(obj.id))
#                     obj.save()

#                     inventory = Inventory.objects.create(product=obj,
#                                                             safety_quantity=form.cleaned_data['safety_quantity'],
#                                                             )
#                     inventory.save()

#                     for file in request.FILES.getlist('product_pic'):
#                         product_pic = ProductPicture.objects.create(
#                             product_id=obj.id)
#                         product_pic.image = file
#                         product_pic.save()

#                 msg = _("product added successfully")
#                 return redirect('product-list')
#             except Exception as e:
#                 raise e
#         else:
#             msg = _("form is invalid")

#     elif request.method == "GET":
#         form = ProductForm()

#     return render(request, 'home/product.html', {"msg": msg, 'form': form})


@login_required(login_url="/login/")
def productCreate(request):
    uoms = []
    product_status_li = []
    currency_of_costs = []
    currencies = []
    brands = []
    created_date = datetime.now().strftime("%Y-%m-%d")
    category_subcategory = {}
    categories = {}
    try:
        product_types = Category.objects.filter(type="Product Category").values("id", "name", "type", "parent_id", "parent__type", "parent__name").order_by("-id")
        for prod_type in product_types:
            if not prod_type["parent_id"]:
                categories[prod_type["id"]] = prod_type["name"]
            else:
                if prod_type["parent_id"] not in category_subcategory:
                    category_subcategory[prod_type["parent_id"]] = [{"id": prod_type["id"], "name": prod_type["name"]}]
                else:
                    category_subcategory[prod_type["parent_id"]].append({"id": prod_type["id"], "name": prod_type["name"]})

        category_subcategory = mark_safe(json.dumps(category_subcategory))

        system_parameters_data = SystemParameters.objects.filter(is_deleted=False).all()
        for system_param in system_parameters_data:
            if str(system_param.system_parameter).lower() == "unit of measurement":
                uoms = str(system_param.name).split(", ")
            # if str(system_param.system_parameter).lower() == "product status":
            #     product_status_li = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "currency":
                currencies = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "currency of cost":
                currency_of_costs = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "brand":
                brands = str(system_param.name).split(", ")

        if request.method == "POST":
            with transaction.atomic():
                brand = request.POST.get("brand")
                category_id = request.POST.get("category")
                sub_category_id = request.POST.get("sub_category")
                barcode = request.POST.get("barcode")
                shelf_life_value = request.POST.get("shelf_life_value") if request.POST.get("shelf_life_value") else None
                shelf_life_time = request.POST.get("shelf_life_time") if shelf_life_value else None
                product_chinese_name = request.POST.get("chinese_product_name")
                product_english_name = request.POST.get("chinese_english_name")
                product_image = request.FILES.get('product_image')
                unit_of_measurement = request.POST.get("unit_of_measurement")
                weight = request.POST.get("weight") if request.POST.get("weight") else None
                onboarding_date = datetime.strptime(str(request.POST.get("onboarding_date")), "%m/%d/%Y").date() if request.POST.get("onboarding_date") else datetime.now().date()
                sales_currency = request.POST.get("currency").upper()
                retail_price = request.POST.get("retail_price") if request.POST.get("retail_price") else None
                selling_price = request.POST.get("selling_price") if request.POST.get("selling_price") else None
                bundle_product_id = request.POST.get("bundle_product_id")
                bundle_product_price = request.POST.get("bundle_product_price") if request.POST.get("bundle_product_price") else None
                cost_of_retail = request.POST.get("cost_of_retail") if request.POST.get("cost_of_retail") else None
                supplier_id = request.POST.get("supplier_id")
                supplier_product_name = request.POST.get("supplier_product_name")
                ingredient = request.POST.get("ingredient")
                product_remark = request.POST.get("product_remark")
                raw_cost = request.POST.get("raw_cost") if request.POST.get("raw_cost") else None
                packaging_cost = request.POST.get("packaging_cost") if request.POST.get("packaging_cost") else None
                processing_cost = request.POST.get("processing_cost") if request.POST.get("processing_cost") else None
                other_cost = request.POST.get("other_cost") if request.POST.get("other_cost") else None
                delivery_fee_to_hk = request.POST.get("delivery_fee_to_hk") if request.POST.get("delivery_fee_to_hk") else None
                total_cost = request.POST.get("total_cost_product") if request.POST.get("total_cost_product") else None
                currency_of_cost = request.POST.get("currency_of_cost").upper()
                safe_number = request.POST.get("safe_number") if request.POST.get("safe_number") else None
                purchasing_amount = request.POST.get("purchasing_amount") if request.POST.get("purchasing_amount") else None
                button_clicked = request.POST.get("button_clicked")

                exist_product = Product.objects.filter(
                            category_id=category_id,
                            sub_category_id=sub_category_id,
                            product_chinese_name=product_chinese_name,
                            unit_of_measurement=unit_of_measurement,
                            sales_currency=sales_currency,
                            supplier_product_name=supplier_product_name,
                            currency_of_cost=currency_of_cost,
                            ).first()

                if exist_product:
                    return render(request, 'home/product.html', {
                                "uoms": uoms,
                                "currency": currencies,
                                "currency_of_costs": currency_of_costs,
                                "created_date": created_date,
                                "role": request.user.role,
                                "logged_in_user_id": request.user.id,
                                "category_subcategory": category_subcategory,
                                "categories": categories,
                                "brands": brands,
                                "error_msg": "Product is already exist."
                                })
                
                status = ""
                if button_clicked and button_clicked == "saveBtn":
                    status = "draft"
                else:
                    current_date = datetime.now().date()
                    if onboarding_date > current_date:
                        status = "in preparation"
                    else:
                        status = "in sales"

                prod_id_pattern = SystemParametersForId.objects.filter(category_id=int(category_id)).values("value").first()
                if not prod_id_pattern or not prod_id_pattern["value"]:
                    category_name = categories[int(category_id)] if int(category_id) in categories else ""
                    return render(request, 'home/product.html', {
                            "uoms": uoms, 
                            "currency": currencies,
                            "currency_of_costs": currency_of_costs,
                            "created_date": created_date,
                            "role": request.user.role,
                            "logged_in_user_id": request.user.id,
                            "category_subcategory": category_subcategory,
                            "categories": categories,
                            "brands": brands,
                            "error_msg": "Please add Product ID pattern in system parameters for category `<b>" + category_name + "</b>`."
                            })

                bundle_prod_id = None
                if bundle_product_id:
                    product = Product.objects.annotate(lower_field=Lower("product_id", output_field=CharField())).filter(lower_field=str(bundle_product_id).lower()).values("id").first()
                    if product:
                        bundle_prod_id = product["id"]

                supp_id = None
                if supplier_id:
                    supplier = Supplier.objects.annotate(lower_field=Lower("supplier_id", output_field=CharField())).filter(lower_field=str(supplier_id).lower()).values("id").first()
                    if supplier:
                        supp_id = supplier["id"]

                product_obj = Product.objects.create(
                    brand=brand,
                    category_id=category_id,
                    sub_category_id=sub_category_id,
                    barcode_no=barcode,
                    shelf_life_value=shelf_life_value,
                    shelf_life_time=shelf_life_time,
                    product_chinese_name=product_chinese_name,
                    product_english_name=product_english_name,
                    unit_of_measurement=unit_of_measurement,
                    unit_weight=weight,
                    status=status,
                    onboarding_date=onboarding_date,
                    sales_currency=sales_currency,
                    retail_price=retail_price,
                    selling_price=selling_price,
                    bundle_product_id=bundle_prod_id,
                    bundle_product_price=bundle_product_price,
                    cost_of_retail=cost_of_retail,
                    supplier_id=supp_id,
                    supplier_product_name=supplier_product_name,
                    ingredient=ingredient,
                    product_remark=product_remark,
                    raw_cost=raw_cost,
                    packaging_cost=packaging_cost,
                    processing_cost=processing_cost,
                    other_cost=other_cost,
                    delivery_fee_to_hk=delivery_fee_to_hk,
                    currency_of_cost=currency_of_cost,
                    total_cost=total_cost,
                    safe_number=safe_number,
                    purchasing_amount=purchasing_amount,
                    created_by=request.user,
                )

                if product_obj:
                    latest_product = Product.objects.filter(product_id__icontains=prod_id_pattern["value"]).values("product_id").order_by("-id").first()
                    latest_pro_id = 1
                    if latest_product:
                        latest_pro_id = int(latest_product["product_id"].replace(prod_id_pattern["value"], "")) + 1
                    product_obj.product_id = prod_id_pattern["value"] + str(latest_pro_id)
                    # product_obj.product_id = prod_id_pattern["value"] + str(product_obj.id)
                    product_obj.save()
                    if product_image:
                        product_file_obj = Product_Files.objects.create(product_id=product_obj.id, file=product_image, file_name=product_image.name)
                        product_file = Product_Files.objects.filter(id=product_file_obj.id).values("file", "file_name").first()
                        file_path = product_file["file"]
                        file_name = product_file["file_name"]
                        bucket_name = settings.MEDIA_BUCKET_NAME
                        object_name = f"{product_obj.id}/{file_name}"
                        is_bucket = storage_backends.create_bucket(bucket_name)
                        if is_bucket:
                            is_file_upload = storage_backends.upload_file(file_path, bucket_name, object_name)

                return redirect("product-list")
        else:
            return render(request, 'home/product.html', {
                "uoms": uoms, 
                "currency": currencies,
                "currency_of_costs": currency_of_costs,
                "created_date": created_date,
                "role": request.user.role,
                "logged_in_user_id": request.user.id,
                "category_subcategory": category_subcategory,
                "categories": categories,
                "brands": brands,
                })
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/product.html', {
                                    "uoms": uoms, 
                                    "currency": currencies,
                                    "currency_of_costs": currency_of_costs,
                                    "created_date": created_date,
                                    "role": request.user.role,
                                    "logged_in_user_id": request.user.id,
                                    "category_subcategory": category_subcategory,
                                    "categories": categories,
                                    "brands": brands,
                                    "error_msg": str(e),
                                    })


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def get_supplier(request):
    try:
        if request.method == "POST":
            supplier_id = request.POST.get("supplier_id")
            supplier = Supplier.objects.annotate(lower_field=Lower('supplier_id', output_field=CharField())).filter(lower_field=str(supplier_id).lower()).values("company_name", "status").first()
            if supplier:
                if supplier["status"] == "draft":
                    return HttpResponse(json.dumps({"code": 0, "msg": "Supplier `<b>" + supplier_id + "</b>` is in draft."}), content_type="json")
                return HttpResponse(json.dumps({"code": 1, "supplier_name": supplier["company_name"]}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Supplier `<b>" + supplier_id + "</b>` does not exist."}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def get_bundle_product(request):
    try:
        if request.method == "POST":
            bundle_product_id = request.POST.get("bundle_product_id")
            product = Product.objects.annotate(lower_field=Lower('product_id', output_field=CharField())).filter(lower_field=str(bundle_product_id).lower()).values("product_chinese_name", "status").first()
            if product:
                if product["status"] == "draft":
                    return HttpResponse(json.dumps({"code": 0, "msg": "Product `<b>" + bundle_product_id + "</b>` is in draft."}), content_type="json")
                return HttpResponse(json.dumps({"code": 1, "product_name": product["product_chinese_name"]}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Product `<b>" + bundle_product_id + "</b>` does not exist."}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@login_required(login_url="/login/")
def productUpdate(request, id):
    try:
        exist_product = Product.objects.filter(id=id).first()
        if exist_product:
            if request.method == "POST":
                with transaction.atomic():
                    brand = request.POST.get("brand")
                    barcode = request.POST.get("barcode")
                    shelf_life_value = request.POST.get("shelf_life_value") if request.POST.get("shelf_life_value") else None
                    shelf_life_time = request.POST.get("shelf_life_time") if shelf_life_value else None
                    product_chinese_name = request.POST.get("chinese_product_name")
                    product_english_name = request.POST.get("chinese_english_name")
                    product_image = request.FILES.get('product_image')
                    unit_of_measurement = request.POST.get("unit_of_measurement")
                    weight = request.POST.get("weight") if request.POST.get("weight") else None
                    onboarding_date = datetime.strptime(str(request.POST.get("onboarding_date_product")), "%Y-%m-%d").date()
                    sales_currency = request.POST.get("currency")
                    retail_price = request.POST.get("retail_price") if request.POST.get("retail_price") else None
                    selling_price = request.POST.get("selling_price") if request.POST.get("selling_price") else None
                    bundle_product_id = request.POST.get("bundle_product_id")
                    bundle_product_price = request.POST.get("bundle_product_price") if request.POST.get("bundle_product_price") else None
                    cost_of_retail = request.POST.get("cost_of_retail") if request.POST.get("cost_of_retail") else None
                    supplier_id = request.POST.get("supplier_id")
                    supplier_product_name = request.POST.get("supplier_product_name")
                    ingredient = request.POST.get("ingredient")
                    product_remark = request.POST.get("product_remark")
                    raw_cost = request.POST.get("raw_cost") if request.POST.get("raw_cost") else None
                    packaging_cost = request.POST.get("packaging_cost") if request.POST.get("packaging_cost") else None
                    processing_cost = request.POST.get("processing_cost") if request.POST.get("processing_cost") else None
                    other_cost = request.POST.get("other_cost") if request.POST.get("other_cost") else None
                    delivery_fee_to_hk = request.POST.get("delivery_fee_to_hk") if request.POST.get("delivery_fee_to_hk") else None
                    total_cost = request.POST.get("total_cost_product") if request.POST.get("total_cost_product") else None
                    currency_of_cost = request.POST.get("currency_of_cost")
                    safe_number = request.POST.get("safe_number") if request.POST.get("safe_number") else None
                    purchasing_amount = request.POST.get("purchasing_amount") if request.POST.get("purchasing_amount") else None
                    button_clicked = request.POST.get("button_clicked")
                    status = request.POST.get("product_status") if request.POST.get("product_status") else None

                    if str(status).lower() == "draft" and button_clicked and button_clicked == "saveBtn":
                        status = "draft"
                    elif str(status).lower() == "draft" and button_clicked and button_clicked == "submitBtn":
                        current_date = datetime.now().date()
                        if onboarding_date > current_date:
                            status = "in preparation"
                        else:
                            status = "in sales"

                    bundle_prod_id = None
                    if bundle_product_id:
                        product = Product.objects.annotate(lower_field=Lower("product_id", output_field=CharField())).filter(lower_field=str(bundle_product_id).lower()).values("id").first()
                        if product:
                            bundle_prod_id = product["id"]

                    supp_id = None
                    if supplier_id:
                        supplier = Supplier.objects.annotate(lower_field=Lower("supplier_id", output_field=CharField())).filter(lower_field=str(supplier_id).lower()).values("id").first()
                        if supplier:
                            supp_id = supplier["id"]

                    product_obj = Product.objects.filter(id=id).update(
                        brand=brand,
                        barcode_no=barcode,
                        shelf_life_value=shelf_life_value,
                        shelf_life_time=shelf_life_time,
                        product_chinese_name=product_chinese_name,
                        product_english_name=product_english_name,
                        unit_of_measurement=unit_of_measurement,
                        unit_weight=weight,
                        status=status,
                        sales_currency=sales_currency,
                        retail_price=retail_price,
                        selling_price=selling_price,
                        bundle_product_id=bundle_prod_id,
                        bundle_product_price=bundle_product_price,
                        cost_of_retail=cost_of_retail,
                        supplier_id=supp_id,
                        supplier_product_name=supplier_product_name,
                        ingredient=ingredient,
                        product_remark=product_remark,
                        raw_cost=raw_cost,
                        packaging_cost=packaging_cost,
                        processing_cost=processing_cost,
                        other_cost=other_cost,
                        delivery_fee_to_hk=delivery_fee_to_hk,
                        currency_of_cost=currency_of_cost,
                        total_cost=total_cost,
                        safe_number=safe_number,
                        purchasing_amount=purchasing_amount,
                    )

                    if product_image:
                        bucket_name = settings.MEDIA_BUCKET_NAME
                        folder_name = id  # This is the "folder" name within the bucket
                        file_path = ""
                        file_name = ""
                        product_file_exist = Product_Files.objects.filter(product_id=id).first()
                        if product_file_exist:
                            old_file_name = str(product_file_exist.file_name)
                            old_file_path = str(product_file_exist.file)
                            product_file_exist.file = product_image
                            product_file_exist.file_name = product_image.name
                            product_file_exist.save()
                            
                            file_path = str(product_file_exist.file)
                            file_name = str(product_file_exist.file_name)
                            object_name = f"{folder_name}/{old_file_name}"
                            is_deleted = storage_backends.delete_file(bucket_name, object_name)
                        else:
                            product_file_obj = Product_Files.objects.create(product_id=id, file=product_image, file_name=product_image.name)
                            product_file = Product_Files.objects.filter(id=product_file_obj.id).values("file", "file_name").first()
                            file_path = product_file["file"]
                            file_name = product_file["file_name"]
                            
                        if file_path and file_name:
                            object_name = f"{folder_name}/{file_name}"
                            is_bucket = storage_backends.create_bucket(bucket_name)
                            if is_bucket:
                                is_file_upload = storage_backends.upload_file(file_path, bucket_name, object_name)

                    return redirect("product-list")
            else:
                name_card_data = Product_Files.objects.filter(product_id=exist_product.id).first()
                is_out_of_stock = False
                inventory = Inventory.objects.filter(product_id=exist_product.id).values("current_quantity").first()
                if inventory and inventory["current_quantity"] <= 0:
                    is_out_of_stock = True
                    
                inv_po_items = InventoryPurchaseOrderItems.objects.filter(product_id=exist_product.id).aggregate(total_po_quantity=Sum('quantity'))
                total_product_stock_move = StockMove.objects.filter(product_id=exist_product.id).aggregate(total_quantity=Sum('quantity'))
                total_order_quantity = inv_po_items["total_po_quantity"] if inv_po_items["total_po_quantity"] else 0
                if total_product_stock_move:
                    total_order_quantity = inv_po_items["total_po_quantity"] - total_product_stock_move['total_quantity'] if inv_po_items["total_po_quantity"] and total_product_stock_move['total_quantity'] else total_order_quantity
                
                total_stock_in = 0
                total_product_stock_in = StockMove.objects.filter(product_id=exist_product.id).exclude(move_type__in=["Depreciation", "depreciation"]).aggregate(total_quantity=Sum('quantity'))
                if total_product_stock_in and total_product_stock_in["total_quantity"]:
                    total_stock_in = total_product_stock_in["total_quantity"]
                    
                stockmove = StockMove.objects.filter(product_id=exist_product.id).exclude(move_type__in=["Depreciation", "depreciation"]).values("created_date").order_by("-id").first()
                    
                total_stock_out = 0
                order_qtys = Orderitems.objects.filter(product_id=exist_product.id).aggregate(total_quantity=Sum('quantity'))
                if order_qtys:
                    total_stock_out = order_qtys["total_quantity"]
                
                last_purchase_date = ""
                latest_order = Orderitems.objects.filter(product_id=exist_product.id).values("created_date").order_by("-id").first()
                if latest_order:
                    last_purchase_date = datetime.strptime(str(latest_order["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if latest_order["created_date"] else ""
                
                last_order_date = ""
                latest_po_order = InventoryPurchaseOrderItems.objects.filter(product_id=exist_product.id).values("created_date").order_by("-id").first()
                if latest_po_order:
                    last_order_date = datetime.strptime(str(latest_po_order["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if latest_po_order["created_date"] else ""
                
                uoms = []
                product_status_li = []
                currency_of_costs = []
                currencies = []
                brands = []
                category_subcategory = {}
                categories = {}
                product_types = Category.objects.filter(type="Product Category").values("id", "name", "type", "parent_id", "parent__type", "parent__name").order_by("-id")
                for prod_type in product_types:
                    if not prod_type["parent_id"]:
                        categories[prod_type["id"]] = prod_type["name"]
                    else:
                        if prod_type["parent_id"] not in category_subcategory:
                            category_subcategory[prod_type["parent_id"]] = [{"id": prod_type["id"], "name": prod_type["name"]}]
                        else:
                            category_subcategory[prod_type["parent_id"]].append({"id": prod_type["id"], "name": prod_type["name"]})

                system_parameters_data = SystemParameters.objects.filter(is_deleted=False).all()
                for system_param in system_parameters_data:
                    if str(system_param.system_parameter).lower() == "unit of measurement":
                        uoms = str(system_param.name).split(", ")
                    # if str(system_param.system_parameter).lower() == "product status":
                    #     product_status_li = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "currency":
                        currencies = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "currency of cost":
                        currency_of_costs = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "brand":
                        brands = str(system_param.name).split(", ")

                base64_with_prefix = ""
                if name_card_data:
                    file_path = str(name_card_data.file)
                    bucket_name = settings.MEDIA_BUCKET_NAME
                    file_name = str(name_card_data.file_name)
                    object_name = f"{id}/{file_name}"
                    base64_with_prefix = storage_backends.get_file(bucket_name, object_name)
                    # if os.path.exists(file_path):
                    #     with open(file_path, "rb") as file:
                    #         image_data = file.read()
                    #         base64_str = base64.b64encode(image_data).decode("utf-8")
                    #         base64_with_prefix = "data:image/jpeg;base64," + base64_str 

                product_data = {
                    "id": exist_product.id,
                    "brand": exist_product.brand if exist_product.brand else "",
                    "category": exist_product.category.name,
                    "sub_category": exist_product.sub_category.name,
                    "product_id": exist_product.product_id,
                    "barcode": exist_product.barcode_no if exist_product.barcode_no else "",
                    "shelf_life_value": exist_product.shelf_life_value if exist_product.shelf_life_value else "",
                    "shelf_life_time": exist_product.shelf_life_time if exist_product.shelf_life_time else "",
                    'product_chinese_name': exist_product.product_chinese_name,
                    'product_english_name': exist_product.product_english_name if exist_product.product_english_name else "",
                    "unit_of_measurement": exist_product.unit_of_measurement if exist_product.unit_of_measurement else "",
                    "weight": exist_product.unit_weight if exist_product.unit_weight else "",
                    "onboarding_date": str(exist_product.onboarding_date),
                    "status": exist_product.status,
                    "currency": exist_product.sales_currency,
                    "retail_price": round(exist_product.retail_price, 2),
                    "selling_price": round(exist_product.selling_price, 2),
                    "bundle_product_id": exist_product.bundle_product.product_id if exist_product.bundle_product and exist_product.bundle_product.product_id else "",
                    "bundle_product_name": exist_product.bundle_product.product_chinese_name if exist_product.bundle_product and exist_product.bundle_product.product_chinese_name else "",
                    "bundle_product_price": round(exist_product.bundle_product_price, 2) if exist_product.bundle_product_price else "",
                    "cost_of_retail": round(exist_product.cost_of_retail, 2),
                    "supplier_id": exist_product.supplier.supplier_id if exist_product.supplier else "",
                    "supplier__company_name": exist_product.supplier.company_name if exist_product.supplier else "",
                    "supplier_product_name": exist_product.supplier_product_name if exist_product.supplier else "",
                    "ingredient": exist_product.ingredient if exist_product.ingredient else "",
                    "product_remark": exist_product.product_remark if exist_product.product_remark else "",
                    "raw_cost": round(exist_product.raw_cost, 2) if exist_product.raw_cost else "",
                    "packaging_cost": round(exist_product.packaging_cost, 2) if exist_product.packaging_cost else "",
                    "processing_cost": round(exist_product.processing_cost, 2) if exist_product.processing_cost else "",
                    "other_cost": round(exist_product.other_cost, 2) if exist_product.other_cost else "",
                    "delivery_fee_to_hk": round(exist_product.delivery_fee_to_hk, 2) if exist_product.delivery_fee_to_hk else "",
                    "currency_of_cost": exist_product.currency_of_cost if exist_product.currency_of_cost else "",
                    "total_cost": round(exist_product.total_cost, 2) if exist_product.total_cost else "",
                    "safe_number": exist_product.safe_number if exist_product.safe_number else "",
                    "purchasing_amount": round(exist_product.purchasing_amount, 2) if exist_product.purchasing_amount else "",
                    "name_card_file_name": name_card_data.file_name if name_card_data and name_card_data.file_name else "",
                    "name_card_file_path": base64_with_prefix,
                    "total_order_quantity": total_order_quantity,
                    "last_purchase_date": last_purchase_date,
                    "last_order_date": last_order_date,
                    "current_inventory": inventory["current_quantity"] if inventory and inventory["current_quantity"] else 0,
                    "total_stock_in": total_stock_in,
                    "total_stock_out": total_stock_out,
                    "last_stock_in_date": datetime.strptime(str(stockmove["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if stockmove else "",
                }

                return render(request, 'home/product_details.html', {
                    "product_data": product_data,
                    "role": request.user.role,
                    "uoms": uoms,
                    # "product_status_li": product_status_li,
                    "currency_of_costs": currency_of_costs,
                    "currency": currencies,
                    "categories": categories,
                    "category_subcategory": category_subcategory,
                    "brands": brands,
                    "is_out_of_stock": is_out_of_stock,
                    })

        return HttpResponse(json.dumps({"code": 0, "msg": "Product does not exist."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


# @login_required(login_url="/login/")
# def productUpdate(request, id):
#     msg = ''
#     product = Product.objects.filter(id=id)
#     form = ProductForm()
#     if not product:
#         msg = _("product not found")

#     else:
#         product = product.first()
#         inventory = Inventory.objects.get(product_id=id)
#         category_id = None
#         if product.category:
#             category_id = product.category.id
#         sub_category_id = None
#         if product.sub_category:
#             sub_category_id = product.sub_category.id
#         supplier_id=None
#         if product.supplier:
#             supplier_id = product.supplier.id
#         form = ProductForm(initial={
#             'category_id': category_id,
#             'sub_category_id':sub_category_id,
#             'product_id': product.product_id,
#             'barcode_no': product.barcode_no,
#             'brand': product.brand,
#             'product_chinese_name': product.product_chinese_name,
#             'product_english_name': product.product_english_name,
#             'supplier_product_name': product.supplier_product_name,
#             'unit_of_measurement': product.unit_of_measurement,
#             'unit_weight_category': product.unit_weight_category,
#             'unit_weight': product.unit_weight,
#             'status': product.status,
#             'supplier_id':supplier_id,
#             'sales_currency': product.sales_currency,
#             'retail_price': product.retail_price,
#             'selling_price': product.selling_price,
#             'std_cost_of_sales': product.std_cost_of_sales,
#             'safety_quantity': inventory.safety_quantity,
#             'shelf_life':product.shelf_life,
#             'ingredient_list':product.ingredient_list,
#         })

#         if request.method == "POST":
#             form = ProductForm(request.POST, instance=product)
#             if form.is_valid():
#                 try:
#                     obj = form.save(commit=False)
#                     obj.specifications = f"{form.cleaned_data['unit_weight']}{form.cleaned_data['unit_of_measurement']}"
#                     if obj.status == "On Sale":
#                         obj.shelf_date = datetime.now().date()
                    
#                     if request.FILES.getlist('product_pic'):
#                         ProductPicture.objects.filter(product_id=id).delete()
                        
#                     for file in request.FILES.getlist('product_pic'):
                        
#                         product_pic = ProductPicture.objects.create(
#                             product_id=obj.id)
#                         product_pic.image = file
#                         product_pic.save()
#                     obj.save()

#                     msg = "product updated successfully"
#                     inventory = Inventory.objects.filter(product_id=obj.id)
#                     inventory.update(product=obj,
#                                         safety_quantity=form.cleaned_data[
#                                             'safety_quantity'],
#                                         )

#                     redirect('/product-list')
#                 except Exception as e:
#                     raise e
#             else:
#                 msg = _("form is invalid")
#     return render(request, 'home/product.html', {"msg": msg, 'form': form})


@login_required(login_url="/login/")
def productGet(request, id):
    msg = ''
    product = Product.objects.get(id=id)
    product_pics = product.productpicture_set.all()

    return render(request, 'home/product-detail.html', {"msg": msg, "product": product, "product_images":product_pics})


@login_required(login_url="/login/")
def productDelete(request, id):
    msg = ""
    form = ProductForm()
    try:
        Product.objects.filter(id=id).delete()
        msg = _("product deleted successfully")
    except Exception as e:
        raise e

    products = Inventory.objects.select_related('product').all()
    return render(request, 'home/product-list.html', {"msg": msg, "products": products, 'form': form})


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def product_delete(request):
    try:
        if request.method == "POST":
            product_id = request.POST.get("product_id")
            order_exist = list(Order.objects.filter(orderitems__product_id=product_id).values_list("order_id", flat=True))
            if order_exist:
                msg = "Cannot delete this product because it is used in the Order `<b>" + ", ".join(order_exist) + "</b>`."
                if len(order_exist) > 1:
                    msg = "Cannot delete this product because it is used in the Orders `<b>" + ", ".join(order_exist) + "</b>`."
                return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")
            product_image = Product_Files.objects.filter(product_id=product_id).values("file", "file_name").first()
            Product.objects.filter(id=product_id).delete()
            if product_image:
                utils.remove_file(product_image["file"].replace("/" + product_image["file_name"], ""))
                bucket_name = settings.MEDIA_BUCKET_NAME
                file_name = str(product_image["file_name"])
                object_name = f"{product_id}/{file_name}"

                is_deleted = storage_backends.delete_file(bucket_name, object_name)

            return HttpResponse(json.dumps({"code": 1, "msg": "Success!"}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json") 


# @login_required(login_url="/login/")
# def exporttocsv(request):
#     msg=""
#     products = Inventory.objects.select_related('product').all()
#     data_dict = {
#         "Product No":[],
#         "Name":[],
#         "English Name":[],
#         "Main Category":[],
#         "Sub Category":[],
#         "Specification":[],
#         "Retail Price":[],
#         "Recommended Selling Price":[],
#         "Cost of Sales":[],
#         "Total Stock-out Quantity":[],
#         "Total Shipment Quantity":[],
#         "Current Inventory Quantity":[],
#         "Total Orderd Quantity":[],
#         "Last Purchase Date":[],
#         "Status":[],


#     }
#     for inventory in products:
#         data_dict['Product No'].append(inventory.product.product_id)
#         data_dict['Name'].append(inventory.product.product_chinese_name)
#         data_dict['English Name'].append(inventory.product.product_english_name)
#         data_dict['Main Category'].append(inventory.product.category)
#         data_dict['Sub Category'].append(inventory.product.sub_category)
#         data_dict['Specification'].append(inventory.product.specifications)
#         data_dict['Retail Price'].append(inventory.product.retail_price)
#         data_dict['Recommended Selling Price'].append(inventory.product.selling_price)
#         data_dict['Cost of Sales'].append(inventory.product.std_cost_of_sales)
#         data_dict['Total Stock-out Quantity'].append(inventory.total_stock_out_quantity)
#         data_dict['Total Shipment Quantity'].append(inventory.total_shipping_quantity)
#         data_dict['Current Inventory Quantity'].append(inventory.current_quantity)
#         data_dict['Total Orderd Quantity'].append(inventory.total_purchased_quantity)
#         data_dict['Last Purchase Date'].append(inventory.last_purchase_date)
#         data_dict['Status'].append(inventory.product.status)
#     df = pd.DataFrame(data_dict)

#     if not Path(f'media/temp/').exists():
#         os.mkdir(f"media/temp/")
    
#     if not Path(f'media/temp/{request.user.id}/').exists():
#         os.mkdir(f"media/temp/{request.user.id}/")

#     now = datetime.now().strftime("%d%m%Y%H%M%S")
    
#     df.to_excel(f"media/temp/{request.user.id}/export_{now}.xlsx")        

#     response = FileResponse(open(f"media/temp/{request.user.id}/export_{now}.xlsx", 'rb'), content_type='text/csv')
#     response['Content-Disposition'] = f'attachment; filename="export_{now}.xlsx"'
    # return response


@login_required(login_url="/login/")
def importfromcsv(request):
    form = importForm()
    msg=''

    if request.method == 'POST':
        form = importForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']

            if not Path('media/').exists():
                os.mkdir('media/')

            if not Path('media/temp/').exists():
                os.mkdir('media/temp/')
            file_path = 'media/temp/' + file.name
            with open(file_path, 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            df = pd.read_excel(file)
            product_to_insert = []
            with transaction.atomic():
                for _, row in df.iterrows():

                    if 'Main Category' in row:
                        category, created = Category.objects.get_or_create(name=row['Main Category'])
                    else:
                        category = None

                    if 'Sub Category' in row:
                        sub_category, created = Category.objects.get_or_create(name=row['Sub Category'])
                    else:
                        sub_category = None

                    if 'Unit Weight' in row and 'Unit Weight Category' in row:
                        specifications = f"{row['Unit Weight']} {row['Unit Weight Category']}"
                    else:
                        specifications = None

                    if str(row['English Name'])=='nan':
                        row['English Name']=None

                    product, created = Product.objects.update_or_create(
                        product_id=row['Product No'] if 'Product No' in row else None,
                        defaults={"category":category,
                        "sub_category":sub_category,
                        "brand":row['Brand Category'] if 'Brand Category' in row else None,
                        "product_chinese_name":row['Name'] if 'Name' in row else None,
                        "product_english_name":row['English Name'] if 'English Name' in row else None,
                        "supplier_product_name":row['Supplier Product Name'] if 'Supplier Product Name' in row else None,
                        "specifications":specifications,
                        "unit_of_measurement":row['Unit Of Measurement'] if 'Unit Of Measurement' in row else None,
                        "unit_weight_category":row['Unit Weight Category'] if 'Unit Weight Category' in row else None,
                        "unit_weight":row['Unit Weight'] if 'Unit Weight' in row else None,
                        "status":row['Status'] if 'Status' in row else None,
                        "sales_currency":row['Sales Currency'] if 'Sales Currency' in row else None,
                        "retail_price":row['Retail Price'] if 'Retail Price' in row else None,
                        "selling_price":row['Recommended Selling Price'] if 'Recommended Selling Price' in row else None,
                        "std_cost_of_sales":row['Cost of Sales'] if 'Cost of Sales' in row else None,
                        "shelf_life":row['Shelf life'] if 'Shelf life' in row else None,
                    })

                    if created:
                        product.product_id = str(product.category.name[0:2].upper()) + str('{:07d}'.format(product.id))
                        product.save()
                        inventory = Inventory.objects.create(product=product)
                        inventory.save()
        
            msg = "File is processing. products will update after few minutes"

            return render(request,'home/import.html', {"form":form, "msg":msg})
    else:
        form = importForm()        

    return render(request,'home/import.html', {"form":form})


@login_required(login_url="/login/")
def download_product_image(request, id):
    try:
        name_card = Product_Files.objects.filter(product_id=id).values("file", "file_name").first()
        if name_card:
            file_path = name_card["file"]
            bucket_name = settings.MEDIA_BUCKET_NAME
            file_name = name_card["file_name"]
            local_file_name = name_card["file_name"]
            
            folder_name = id 
            object_name = f"{folder_name}/{file_name}"

            response = storage_backends.download_file(bucket_name, object_name, local_file_name)
            if response.status_code == 200:
                return response

            return HttpResponse(json.dumps({"code": 0, "msg": "File not found."}), content_type="json")
        # if os.path.exists(file_path):
        #     with open(file_path, 'rb') as file:   
        #         response = HttpResponse(file.read())
        #         response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(str(file_path))
        #         return response
        else:
            return HttpResponse(json.dumps({"code": 0, "msg": "File not found."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def remove_product_image(request):
    try:
        product_id = request.POST.get("product_id")
        name_card = Product_Files.objects.filter(product_id=product_id).first()
        if name_card:
            file_path = str(name_card.file)
            file_path = file_path.replace("/" + os.path.basename(str(file_path)), "")
            bucket_name = settings.MEDIA_BUCKET_NAME
            file_name = str(name_card.file_name)
            object_name = f"{product_id}/{file_name}"

            is_deleted = storage_backends.delete_file(bucket_name, object_name)
            # if response == "Success":
            if is_deleted:
                response = utils.remove_file(file_path)
                name_card.delete()
                return HttpResponse(json.dumps({"code": 1, "msg": "File removed."}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "File not found."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")   


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def get_coc_converted_price(request):
    try:
        converted_costs = {}
        if request.method == "POST":
            old_currency = request.POST.get("old_currency")
            new_currency = request.POST.get("new_currency")
            all_costs = json.loads(request.POST.get("all_costs"))

            for key, value in all_costs.items():
                if old_currency and new_currency and value:
                    conv_cost = utils.convert_currency(float(value), old_currency, new_currency)
                    if conv_cost:
                        converted_costs[key] = round(conv_cost, 2)
                else:
                    converted_costs[key] = 0

            return HttpResponse(json.dumps({"code": 1, "converted_costs": converted_costs}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")