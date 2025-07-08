from apps.home.forms.supplierform import SupplierForm
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
import sys, json, os
from django.http import HttpResponse
from apps.home.models import Category, SystemParameters, Purchase, Supplier, Product, PurchaseItems
from apps.home.model.supplier import Supplier_Files
from apps.home.forms.customerform import AREA_CODES
from datetime import datetime
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from django.http import FileResponse
from django.db.models import Q
import base64, traceback
from apps.home.crud import utils
from django.conf import settings
from apps.home.crud import storage_backends, manager


@login_required(login_url="/login/")
def supplierList(request):
    form = SupplierForm()
    suppliers_data = []
    try:
        suppliers = Supplier.objects.values(
            "id",
            "supplier_id",
            "supplier_type",
            "product_type",
            "company_name",
            "location",
            "currency",
            "prefix",
            "contact_type",
            "contact_person_1",
            "phone_1",
            "contact_person_2",
            "phone_2",
            "email",
            "website",
            "remark",
            "purchasing_comments",
            "status",
            "created_by",
            "created_date",
            "last_po_date",
            "status",
        ).order_by("-id")

        supplier_ids = list(suppliers.values_list("id", flat=True))
        supplier_wise_file = {}
        supplier_files = Supplier_Files.objects.filter(supplier_id__in=supplier_ids).values("supplier_id", "file", "file_name")
        for supp_file in supplier_files:
            if supp_file["supplier_id"] not in supplier_wise_file:
                supplier_wise_file[supp_file["supplier_id"]] = {"file_path": supp_file["file"], "file_name": supp_file["file_name"]}

        supplier_po_no_cost = {}
        supplier_last_po_date = {}
        supplier_product_ids = list(Product.objects.filter(supplier_id__in=supplier_ids).values_list("id", flat=True))
        po_items = PurchaseItems.objects.filter(product_id__in=supplier_product_ids).prefetch_related('purchases')
        for po_item in po_items:
            purchase_orders = po_item.purchases.all()
            supplier_id = po_item.product.supplier_id
            po_ids = []
            no_of_order_count = 0
            total_cost = 0
            for po in purchase_orders:
                if po.id not in po_ids:
                    po_ids.append(po.id)
                    no_of_order_count += 1
                    total_cost += float(po.total_cost) if po.total_cost else 0
            if supplier_id not in supplier_po_no_cost:
                supplier_po_no_cost[supplier_id] = {"no_of_order_count": no_of_order_count, "total_cost": total_cost}
            else:
                supplier_po_no_cost[supplier_id]["no_of_order_count"] += no_of_order_count
                supplier_po_no_cost[supplier_id]["total_cost"] += total_cost
                
            last_po_date = ""
            if po_ids:
                last_po_frm_supp = Purchase.objects.filter(id__in=po_ids).values("created_date").order_by("-id").first()
                last_po_date = datetime.strptime(str(last_po_frm_supp["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")
                supplier_last_po_date[supplier_id] = last_po_date

        for supplier in suppliers:
            base64_with_prefix = ""
            if supplier["id"] in supplier_wise_file:
                file_path = str(supplier_wise_file[supplier["id"]]["file_path"])
                bucket_name = settings.MEDIA_BUCKET_NAME
                file_name = str(supplier_wise_file[supplier["id"]]["file_name"])
                supplier_id = supplier["id"]
                object_name = f"{supplier_id}/{file_name}"
                base64_with_prefix = storage_backends.get_file(bucket_name, object_name)
                # if os.path.exists(file_path):
                #     with open(file_path, "rb") as file:
                #         image_data = file.read()
                #         base64_str = base64.b64encode(image_data).decode("utf-8")
                #         base64_with_prefix = "data:image/jpeg;base64," + base64_str 

            suppliers_data.append({
                "id": supplier["id"],
                "supplier_id": supplier["supplier_id"],
                "supplier_type": supplier["supplier_type"],
                "product_type": ", ".join(eval(supplier["product_type"])),
                "company_name": supplier["company_name"],
                "location": supplier["location"],
                "currency": supplier["currency"],
                "prefix": "+" + str(supplier["prefix"]) if "+" not in str(supplier["prefix"]) else supplier["prefix"],
                "contact_type": supplier["contact_type"],
                "contact_person_1": supplier["contact_person_1"],
                "phone_1": supplier["phone_1"] if supplier["phone_1"] else "-",
                "contact_person_2": supplier["contact_person_2"] if supplier["contact_person_2"] else "-",
                "phone_2": supplier["phone_2"] if supplier["phone_2"] else "-",
                "email": supplier["email"] if supplier["email"] else "-",
                "website": supplier["website"] if supplier["website"] else "-",
                "remark": supplier["remark"] if supplier["remark"] else "-",
                "purchasing_comments": supplier["purchasing_comments"] if supplier["purchasing_comments"] else "-",
                "status": supplier["status"] if supplier["status"] else "-",
                "created_date": datetime.strptime(str(supplier["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "last_po_date": supplier_last_po_date[supplier["id"]] if supplier["id"] in supplier_last_po_date and supplier_last_po_date[supplier["id"]] else "-",
                "name_card_file_name": supplier_wise_file[supplier["id"]]["file_name"] if supplier["id"] in supplier_wise_file else "-",
                # "name_card_file_path": "/" + str(supplier_wise_file[supplier["id"]]["file_path"]) if supplier["id"] in supplier_wise_file else "",
                "name_card_file_path": base64_with_prefix,
                "no_of_orders": supplier_po_no_cost[supplier["id"]]["no_of_order_count"] if supplier["id"] in supplier_po_no_cost else "-",
                "total_cost": supplier_po_no_cost[supplier["id"]]["total_cost"] if supplier["id"] in supplier_po_no_cost else "-",
            })

        return render(request, 'home/supplier-list.html', {"suppliers": suppliers_data, 'form': form, "role": request.user.role})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/supplier-list.html', {"suppliers": suppliers_data, 'form': form, "role": request.user.role, "error_msg": str(e)})


@login_required(login_url="/login/")
def supplier_list_export(request):
    try:
        query = Q()
        search_keyword = request.GET["search_keyword"] if "search_keyword" in request.GET else ""
        if search_keyword:
            query.add(Q(supplier_id__icontains=search_keyword) | Q(supplier_type__icontains=search_keyword) |
                      Q(product_type__icontains=search_keyword) | Q(company_name__icontains=search_keyword) |
                      Q(location__icontains=search_keyword) | Q(currency__icontains=search_keyword) |
                      Q(prefix__icontains=search_keyword) | Q(contact_type__icontains=search_keyword) |
                      Q(contact_person_1__icontains=search_keyword) | Q(phone_1__icontains=search_keyword) |
                      Q(contact_person_2__icontains=search_keyword) | Q(phone_2__icontains=search_keyword) |
                      Q(email__icontains=search_keyword) | Q(website__icontains=search_keyword) |
                      Q(remark__icontains=search_keyword) | Q(purchasing_comments__icontains=search_keyword) |
                      Q(status__icontains=search_keyword) | Q(last_po_date__icontains=search_keyword), query.connector)

        suppliers_data = []
        suppliers = Supplier.objects.filter(query).values(
            "id",
            "supplier_id",
            "supplier_type",
            "product_type",
            "company_name",
            "location",
            "currency",
            "prefix",
            "contact_type",
            "contact_person_1",
            "phone_1",
            "contact_person_2",
            "phone_2",
            "email",
            "website",
            "remark",
            "purchasing_comments",
            "status",
            "created_by",
            "created_by__first_name",
            "created_by__last_name",
            "created_date",
            "last_po_date",
            "status",
        ).order_by("-id")

        supplier_ids = list(suppliers.values_list("id", flat=True))
        supplier_wise_file = {}
        supplier_files = Supplier_Files.objects.filter(supplier_id__in=supplier_ids).values("supplier_id", "file", "file_name")
        for supp_file in supplier_files:
            if supp_file["supplier_id"] not in supplier_wise_file:
                supplier_wise_file[supp_file["supplier_id"]] = {"file_path": supp_file["file"], "file_name": supp_file["file_name"]}

        supplier_po_no_cost = {}
        supplier_last_po_date = {}
        supplier_product_ids = list(Product.objects.filter(supplier_id__in=supplier_ids).values_list("id", flat=True))
        po_items = PurchaseItems.objects.filter(product_id__in=supplier_product_ids).prefetch_related('purchases')
        for po_item in po_items:
            purchase_orders = po_item.purchases.all()
            supplier_id = po_item.product.supplier_id
            po_ids = []
            no_of_order_count = 0
            total_cost = 0
            for po in purchase_orders:
                if po.id not in po_ids:
                    po_ids.append(po.id)
                    no_of_order_count += 1
                    total_cost += float(po.total_cost) if po.total_cost else 0
            if supplier_id not in supplier_po_no_cost:
                supplier_po_no_cost[supplier_id] = {"no_of_order_count": no_of_order_count, "total_cost": total_cost}
            else:
                supplier_po_no_cost[supplier_id]["no_of_order_count"] += no_of_order_count
                supplier_po_no_cost[supplier_id]["total_cost"] += total_cost
                
            last_po_date = ""
            if po_ids:
                last_po_frm_supp = Purchase.objects.filter(id__in=po_ids).values("created_date").order_by("-id").first()
                last_po_date = datetime.strptime(str(last_po_frm_supp["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")
                supplier_last_po_date[supplier_id] = last_po_date

        for supplier in suppliers:
            created_by = ""
            if supplier["created_by"]:
                first_name = supplier["created_by__first_name"]
                last_name = supplier["created_by__last_name"]
                created_by = utils.get_user_full_name(first_name, last_name)
            suppliers_data.append({
                "Created Date": datetime.strptime(str(supplier["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "Company Name": supplier["company_name"],
                "Supplier Type": supplier["supplier_type"],
                "Product Type": ", ".join(eval(supplier["product_type"])),
                "Contact Person 1": supplier["contact_person_1"],
                "Phone 1": supplier["phone_1"] if supplier["phone_1"] else "",
                "Last Purchase Order Date": supplier_last_po_date[supplier["id"]] if supplier["id"] in supplier_last_po_date and supplier_last_po_date[supplier["id"]] else "",
                "Accumlated": supplier_po_no_cost[supplier["id"]]["total_cost"] if supplier["id"] in supplier_po_no_cost else "",
                "No.of Orders": supplier_po_no_cost[supplier["id"]]["no_of_order_count"] if supplier["id"] in supplier_po_no_cost else "",
                "Purchasing Comments": supplier["purchasing_comments"] if supplier["purchasing_comments"] else "",
                "Remark": supplier["remark"] if supplier["remark"] else "",
                "Contact Type": supplier["contact_type"],
                "Contact Person 2": supplier["contact_person_2"] if supplier["contact_person_2"] else "",
                "Phone 2": supplier["phone_2"] if supplier["phone_2"] else "",
                "Email": supplier["email"] if supplier["email"] else "",
                "Website": supplier["website"] if supplier["website"] else "",
                "Location": supplier["location"],
                "Currency": supplier["currency"],
                "Prefix": "+" + str(supplier["prefix"]) if "+" not in str(supplier["prefix"]) else supplier["prefix"],
                "Supplier ID": supplier["supplier_id"],
                "Name Card": supplier_wise_file[supplier["id"]]["file_name"] if supplier["id"] in supplier_wise_file else "",
                "Status": supplier["status"] if supplier["status"] else "",
                "Created By": created_by,
            })

        df = pd.DataFrame(suppliers_data)

        now = datetime.now().strftime("%d%m%Y")
        file_path = 'media/temp/suppliers/' + str(request.user.id) + "/"
        file_name = "suppliers_" + str(now) + ".xlsx"
        full_file_path = file_path + file_name
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        df.to_excel(full_file_path, index=False)        

        response = FileResponse(open(full_file_path, 'rb'), content_type='text/xlsx')
        response['Content-Disposition'] = f'attachment; filename=' + file_name
        return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/supplier-list.html', {"error_msg": str(e)})


@login_required(login_url="/login/")
def SupplierCreate(request):
    supplier_wise_product = {}
    supplier_types_li = []
    locations = []
    contact_types = []
    currencies = []
    prefixes = []
    created_date = datetime.now().strftime("%Y-%m-%d")
    # last_po_date = ""
    try:
        check_exist_supplier = Supplier.objects.values("id").order_by("-id").first()
        supplier_id = 1
        if check_exist_supplier:
            supplier_id = check_exist_supplier["id"] + 1

        # last_purchase_order = Purchase.objects.order_by("-id").first()
        # if last_purchase_order:
        #     last_po_date = datetime.strptime(str(last_purchase_order.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")

        supplier_types = Category.objects.filter(type__in=["Supplier Category", "Product Category"]).values("id", "name", "type", "parent_id", "parent__type", "parent__name").order_by("-id")
        for supp_type in supplier_types:
            if supp_type["type"] == "Supplier Category":
                supplier_types_li.append(supp_type["name"])
            if supp_type["parent__type"] == "Supplier Category":
                if supp_type["parent__name"] not in supplier_wise_product:
                    supplier_wise_product[supp_type["parent__name"]] = [supp_type["name"]]
                else:
                    supplier_wise_product[supp_type["parent__name"]].append(supp_type["name"])

        # system_parameters = {}
        system_parameters_data = SystemParameters.objects.filter(is_deleted=False).all()
        for system_param in system_parameters_data:
            if str(system_param.system_parameter).lower() == "location":
                locations = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "contact type":
                contact_types = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "currency":
                currencies = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "prefix":
                prefixes = str(system_param.name).split(", ")
            # if system_param.system_parameter not in system_parameters:
            #     system_parameters[str(system_param.system_parameter).lower()] = [system_param.name]
            # else:
            #     system_parameters[str(system_param.system_parameter).lower()].append(system_param.name)

        if request.method == "POST":
            with transaction.atomic():
                product_type = request.POST.getlist("product_type")
                location = request.POST.get("location")
                contact_type = request.POST.get("contact_type")
                contact_person_2 = request.POST.get("contact_person_2")
                website = request.POST.get("website")
                company_name = request.POST.get("company_name")
                currency = request.POST.get("currency")
                contact_person_1 = request.POST.get("contact_person_1")
                phone_2 = request.POST.get("phone_2")
                remark = request.POST.get("remark")
                supplier_type = request.POST.get("supplier_type")
                name_card_file = request.FILES.get('name_card_file')
                prefix = "+" + str(request.POST.get("prefix")) if "+" not in str(request.POST.get("prefix")) else request.POST.get("prefix")
                phone_1 = request.POST.get("phone_1")
                email = request.POST.get("email")
                purchasing_comments = request.POST.get("purchasing_comments")
                button_clicked = request.POST.get("button_clicked")

                exist_supplier = Supplier.objects.filter(
                            supplier_type=supplier_type,
                            product_type=product_type,
                            company_name=company_name,
                            location=location,
                            currency=currency,
                            contact_type=contact_type,
                            contact_person_1=contact_person_1,
                            prefix=prefix,
                            ).first()

                if exist_supplier:
                    # return render(request, 'home/supplier.html', {"error_msg": "Supplier is already exist."})
                    return render(request, 'home/supplier.html', {
                                "supplier_types_li": supplier_types_li, 
                                "supplier_wise_product": json.dumps(supplier_wise_product), 
                                "area_codes": AREA_CODES, 
                                "locations": locations, 
                                "contact_types": contact_types, 
                                "currency": currencies,
                                "created_date": created_date,
                                "supplier_id": supplier_id,
                                "prefixes": prefixes,
                                # "last_po_date": last_po_date,
                                "role": request.user.role,
                                "error_msg": "Supplier is already exist."
                                })

                supplier_obj = Supplier.objects.create(
                    supplier_type=supplier_type,
                    product_type=product_type,
                    company_name=company_name,
                    location=location,
                    currency=currency,
                    prefix=prefix,
                    contact_type=contact_type,
                    contact_person_1=contact_person_1,
                    phone_1=phone_1,
                    contact_person_2=contact_person_2,
                    phone_2=phone_2,
                    email=email,
                    website=website,
                    remark=remark,
                    purchasing_comments=purchasing_comments,
                    status="draft" if button_clicked and button_clicked == "saveBtn" else "",
                    created_by=request.user,
                    # last_po_date=last_purchase_order.created_date if last_purchase_order and last_purchase_order.created_date else None,
                )

                if supplier_obj:
                    supplier_obj.supplier_id = f"S{supplier_obj.id:05}"
                    supplier_obj.save()
                    if name_card_file:
                        supplier_file_obj = Supplier_Files.objects.create(supplier_id=supplier_obj.id, file=name_card_file, file_name=name_card_file.name)
                        supplier_file = Supplier_Files.objects.filter(id=supplier_file_obj.id).values("file", "file_name").first()
                        file_path = supplier_file["file"]
                        file_name = supplier_file["file_name"]
                        bucket_name = settings.MEDIA_BUCKET_NAME
                        object_name = f"{supplier_obj.id}/{file_name}"
                        is_bucket = storage_backends.create_bucket(bucket_name)
                        if is_bucket:
                            is_file_upload = storage_backends.upload_file(file_path, bucket_name, object_name)

                return redirect("supplier-list")
        else:
            return render(request, 'home/supplier.html', {
                "supplier_types_li": supplier_types_li, 
                "supplier_wise_product": json.dumps(supplier_wise_product), 
                "area_codes": AREA_CODES, 
                "locations": locations, 
                "contact_types": contact_types, 
                "currency": currencies,
                "created_date": created_date,
                "supplier_id": supplier_id,
                "prefixes": prefixes,
                # "last_po_date": last_po_date,
                "role": request.user.role,
                })
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/supplier.html', {
                                    "supplier_types_li": supplier_types_li, 
                                    "supplier_wise_product": json.dumps(supplier_wise_product), 
                                    "area_codes": AREA_CODES, 
                                    "locations": locations, 
                                    "contact_types": contact_types, 
                                    "currency": currencies,
                                    "created_date": created_date,
                                    # "supplier_id": supplier_id,
                                    # "last_po_date": last_po_date,
                                    "role": request.user.role,
                                    "error_msg": str(e),
                                    })


@login_required(login_url="/login/")
def supplierUpdate(request, id):
    try:
        exist_supplier = Supplier.objects.filter(id=id).first()
        if exist_supplier:
            if request.method == "POST":
                with transaction.atomic():
                    product_type = request.POST.getlist("product_type")
                    location = request.POST.get("location")
                    contact_type = request.POST.get("contact_type")
                    contact_person_2 = request.POST.get("contact_person_2")
                    website = request.POST.get("website")
                    company_name = request.POST.get("company_name")
                    currency = request.POST.get("currency")
                    contact_person_1 = request.POST.get("contact_person_1")
                    phone_2 = request.POST.get("phone_2")
                    remark = request.POST.get("remark")
                    supplier_type = request.POST.get("supplier_type")
                    name_card_file = request.FILES.get('name_card_file')
                    prefix = request.POST.get("prefix")
                    phone_1 = request.POST.get("phone_1")
                    email = request.POST.get("email")
                    purchasing_comments = request.POST.get("purchasing_comments")
                    button_clicked = request.POST.get("button_clicked")

                    Supplier.objects.filter(id=id).update(
                        supplier_type=supplier_type,
                        product_type=product_type,
                        company_name=company_name,
                        location=location,
                        currency=currency,
                        prefix=prefix,
                        contact_type=contact_type,
                        contact_person_1=contact_person_1,
                        phone_1=phone_1,
                        contact_person_2=contact_person_2,
                        phone_2=phone_2,
                        email=email,
                        website=website,
                        remark=remark,
                        purchasing_comments=purchasing_comments,
                        status="draft" if button_clicked and button_clicked == "saveBtn" and exist_supplier.status == "draft" else "",
                    )

                    if name_card_file:
                        bucket_name = settings.MEDIA_BUCKET_NAME
                        folder_name = id  # This is the "folder" name within the bucket
                        file_path = ""
                        file_name = ""
                        supplier_file_exist = Supplier_Files.objects.filter(supplier_id=id).first()
                        if supplier_file_exist:
                            old_file_name = str(supplier_file_exist.file_name)
                            old_file_path = str(supplier_file_exist.file)
                            supplier_file_exist.file = name_card_file
                            supplier_file_exist.file_name = name_card_file.name
                            supplier_file_exist.save()
                            
                            file_path = str(supplier_file_exist.file)
                            file_name = str(supplier_file_exist.file_name)
                            object_name = f"{folder_name}/{old_file_name}"
                            is_deleted = storage_backends.delete_file(bucket_name, object_name)
                        else:
                            supplier_file_obj = Supplier_Files.objects.create(supplier_id=id, file=name_card_file, file_name=name_card_file.name)
                            supplier_file = Supplier_Files.objects.filter(id=supplier_file_obj.id).values("file", "file_name").first()
                            file_path = supplier_file["file"]
                            file_name = supplier_file["file_name"]
                        
                        if file_path and file_name:
                            object_name = f"{folder_name}/{file_name}"
                            is_bucket = storage_backends.create_bucket(bucket_name)
                            if is_bucket:
                                is_file_upload = storage_backends.upload_file(file_path, bucket_name, object_name)

                    return redirect("supplier-list")
            else:
                name_card_data = Supplier_Files.objects.filter(supplier_id=exist_supplier.id).first()
                supplier_wise_product = {}
                supplier_types = Category.objects.filter(type__in=["Supplier Category", "Product Category"]).values("id", "name", "type", "parent_id", "parent__type", "parent__name").order_by("-id")
                supplier_types_li = []
                for supp_type in supplier_types:
                    if supp_type["type"] == "Supplier Category":
                        supplier_types_li.append(supp_type["name"])
                    if supp_type["parent__type"] == "Supplier Category":
                        if supp_type["parent__name"] not in supplier_wise_product:
                            supplier_wise_product[supp_type["parent__name"]] = [supp_type["name"]]
                        else:
                            supplier_wise_product[supp_type["parent__name"]].append(supp_type["name"])

                locations = []
                contact_type = []
                currency = []
                prefixes = []
                system_parameters_data = SystemParameters.objects.filter(is_deleted=False).all()
                for system_param in system_parameters_data:
                    if str(system_param.system_parameter).lower() == "location":
                        locations = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "contact type":
                        contact_type = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "currency":
                        currency = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "prefix":
                        prefixes = str(system_param.name).split(", ")

                po_ids = []
                no_of_order_count = 0
                total_cost = 0
                supplier_product_ids = list(Product.objects.filter(supplier_id=id).values_list("id", flat=True))
                po_items = PurchaseItems.objects.filter(product_id__in=supplier_product_ids).prefetch_related('purchases')
                for po_item in po_items:
                    purchase_orders = po_item.purchases.all()
                    for po in purchase_orders:
                        if po.id not in po_ids:
                            po_ids.append(po.id)
                            no_of_order_count += 1
                            total_cost += float(po.total_cost) if po.total_cost else 0
                
                last_po_date = ""
                if po_ids:
                    last_po_frm_supp = Purchase.objects.filter(id__in=po_ids).values("created_date").order_by("-id").first()
                    last_po_date = datetime.strptime(str(last_po_frm_supp["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")

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

                supplier_data = {
                    "id": exist_supplier.id,
                    "supplier_id": exist_supplier.supplier_id,
                    "supplier_type": exist_supplier.supplier_type,
                    "product_type": ", ".join(eval(exist_supplier.product_type)),
                    "company_name": exist_supplier.company_name,
                    "location": exist_supplier.location,
                    "currency": exist_supplier.currency,
                    "prefix": exist_supplier.prefix,
                    "contact_type": exist_supplier.contact_type,
                    "contact_person_1": exist_supplier.contact_person_1,
                    "phone_1": exist_supplier.phone_1 if exist_supplier.phone_1 else "",
                    "contact_person_2": exist_supplier.contact_person_2 if exist_supplier.contact_person_2 else "",
                    "phone_2": exist_supplier.phone_2 if exist_supplier.phone_2 else "",
                    "email": exist_supplier.email if exist_supplier.email else "",
                    "website": exist_supplier.website if exist_supplier.website else "",
                    "remark": exist_supplier.remark if exist_supplier.remark else "",
                    "purchasing_comments": exist_supplier.purchasing_comments if exist_supplier.purchasing_comments else "",
                    "status": exist_supplier.status,
                    "created_date": datetime.strptime(str(exist_supplier.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                    "last_po_date": last_po_date if last_po_date else "",
                    "name_card_file_name": name_card_data.file_name if name_card_data and name_card_data.file_name else "",
                    "name_card_file_path": base64_with_prefix,
                }

                return render(request, 'home/supplier_details.html', {
                    "supplier_data": supplier_data,
                    "supplier_types_li": supplier_types_li,
                    "supplier_wise_product": json.dumps(supplier_wise_product), 
                    "area_codes": AREA_CODES, 
                    "locations": locations, 
                    "contact_types": contact_type, 
                    "currency": currency,
                    "no_of_order_count": no_of_order_count if no_of_order_count > 0 else "",
                    "prefixes": prefixes,
                    "total_cost": total_cost if total_cost > 0 else "",
                    "role": request.user.role,
                    })
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


# @login_required(login_url="/login/")
# def SupplierCreate(request):
#     form = SupplierForm(request.POST)
#     if request.method == "POST":

#         if form.is_valid():
#                 form.save()
#                 messages.success(request, _("Supplier added successfully"))
#                 return redirect('supplier-list')
#         else:
#             messages.error(request, _( "form is invalid"))

#     elif request.method == "GET":
#         form = SupplierForm()

#     return render(request, 'home/supplier.html', {'form': form})


# @login_required(login_url="/login/")
# def supplierUpdate(request, id):
#     msg = ''
#     customer = Supplier.objects.filter(id=id)
#     if not customer:
#         messages.error(request, _("supplier not found"))
#     else:
#         customer = customer.first()
#         form = SupplierForm(instance=customer)
        
#         if request.method == "POST":
#             form = SupplierForm(request.POST, instance=customer)
#             if form.is_valid():
#                     form.save()
#                     messages.success(request, _("Supplier updated successfully"))
#             else:
#                 messages.error(request,  _("form is invalid"))
#     return render(request, 'home/supplier.html', {'form': form})

@login_required(login_url="/login/")
def supplierGet(request, id):
    msg =''
    supplier = Supplier.objects.get(id=id)
    if not supplier:
        msg = _("Supplier not found")
    supplier=supplier.__dict__
    supplier.pop("_state")
    supplier.pop("created_date")    
    supplier.pop("updated_date") 
    # customer = {key.replace("_"," "):customer[key] for key in customer}

    return render(request, 'home/supplier-detail.html', {"msg": msg, "supplier":supplier})


@login_required(login_url="/login/")
def supplierDelete(request, id):
    msg =''
    try:
        supplier = Supplier.objects.filter(id=id).delete()
        msg=_("supplier deleted successfully")

        return redirect("supplier-list")
    except Exception as e:
        pass
    suppliers = Supplier.objects.all()
    return render(request, 'home/supplier-list.html', {"msg": msg, "suppliers":suppliers})


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def supplier_delete(request):
    try:
        if request.method == "POST":
            supplier_id = request.POST.get("supplier_id")
            pro_exist = list(Product.objects.filter(supplier_id=supplier_id).values_list("product_id", flat=True))
            if pro_exist:
                msg = "Cannot delete this supplier because it is used in the Product `<b>" + ", ".join(pro_exist) + "</b>`."
                if len(pro_exist) > 1:
                    msg = "Cannot delete this supplier because it is used in the Products `<b>" + ", ".join(pro_exist) + "</b>`."
                return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")
            supplier_name_card = Supplier_Files.objects.filter(supplier_id=supplier_id).values("file", "file_name").first()
            supplier = Supplier.objects.filter(id=supplier_id).delete()
            if supplier_name_card:
                utils.remove_file(supplier_name_card["file"].replace("/" + os.path.basename(str(supplier_name_card["file"])), ""))
                bucket_name = settings.MEDIA_BUCKET_NAME
                file_name = str(supplier_name_card["file_name"])
                object_name = f"{supplier_id}/{file_name}"

                is_deleted = storage_backends.delete_file(bucket_name, object_name)

            return HttpResponse(json.dumps({"code": 1, "msg": "Success!"}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json") 
    

@login_required(login_url="/login/")
def download_name_card(request, id):
    try:
        name_card = Supplier_Files.objects.filter(supplier_id=id).values("file", "file_name").first()
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
def remove_supplier_name_card(request):
    try:
        supplier_id = request.POST.get("supplier_id")
        name_card = Supplier_Files.objects.filter(supplier_id=supplier_id).first()
        if name_card:
            file_path = str(name_card.file)
            file_path = file_path.replace("/" + os.path.basename(str(file_path)), "")
            bucket_name = settings.MEDIA_BUCKET_NAME
            file_name = str(name_card.file_name)
            object_name = f"{supplier_id}/{file_name}"

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


@login_required(login_url="/login/")
def supplier_import_samplefile(request):
    try:
        full_file_path = 'sample_files/import_suppliers_sample_file.xlsx'
        response = utils.download_samplefile(full_file_path, "import_suppliers_sample_file.xlsx")
        if response:
            return response
        return render(request, 'home/supplier-list.html', {"error_msg": "Sample file not found."})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/supplier-list.html', {"error_msg": str(e)})


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def suppliers_import(request):
    try:
        if request.method == "POST":
            import_supplier_file = request.FILES.get("import_supplier_file")
            if import_supplier_file:
                with transaction.atomic():
                    xlsx_df = pd.read_excel(import_supplier_file)
                    xlsx_df = xlsx_df.map(lambda x: None if pd.isna(x) or x == '' else x)
                    suppliers_dict = xlsx_df.to_dict(orient='records')
                    mandatory_field = []

                    last_purchase_order = Purchase.objects.order_by("-id").first()
                    area_codes = []
                    for key,value in AREA_CODES:
                        area_codes.append(str(key))

                    exist_suppliers = []
                    for supplier in suppliers_dict:
                        company_name = supplier["Company Name"] if "Company Name" in supplier and supplier["Company Name"] else None
                        supplier_type = supplier["Supplier Type"] if "Supplier Type" in supplier and supplier["Supplier Type"] else None
                        product_type = supplier["Product Type"].split(", ") if "Product Type" in supplier and supplier["Product Type"] else None
                        contact_person_1 = supplier["Contact Person 1"] if "Contact Person 1" in supplier and supplier["Contact Person 1"] else None
                        phone_1 = supplier["Phone 1"] if "Phone 1" in supplier and supplier["Phone 1"] else None
                        purchasing_comments = supplier["Purchasing Comments"] if "Purchasing Comments" in supplier and supplier["Purchasing Comments"] else None
                        remark = supplier["Remark"] if "Remark" in supplier and supplier["Remark"] else None
                        contact_type = supplier["Contact Type"] if "Contact Type" in supplier and supplier["Contact Type"] else None
                        contact_person_2 = supplier["Contact Person 2"] if "Contact Person 2" in supplier and supplier["Contact Person 2"] else None
                        phone_2 = supplier["Phone 2"] if "Phone 2" in supplier and supplier["Phone 2"] else None
                        email = supplier["Email"] if "Email" in supplier and supplier["Email"] else None
                        website = supplier["Website"] if "Website" in supplier and supplier["Website"] else None
                        location = supplier["Location"] if "Location" in supplier and supplier["Location"] else None
                        currency = supplier["Currency"] if "Currency" in supplier and supplier["Currency"] else None
                        prefix = str(supplier["Prefix"]) if "Prefix" in supplier and supplier["Prefix"] else None
                        prefix = "+" + str(prefix) if prefix and "+" not in str(prefix) else prefix
                        prefix = prefix if prefix in area_codes else None

                        if not company_name and "Company Name" not in mandatory_field:
                            mandatory_field.append("Company Name")
                        if not supplier_type and "Supplier Type" not in mandatory_field:
                            mandatory_field.append("Supplier Type")
                        if not product_type and "Product Type" not in mandatory_field:
                            mandatory_field.append("Product Type")
                        if not contact_person_1 and "Contact Person 1" not in mandatory_field:
                            mandatory_field.append("Contact Person 1")
                        if not contact_type and "Contact Type" not in mandatory_field:
                            mandatory_field.append("Contact Type")
                        if not location and "Location" not in mandatory_field:
                            mandatory_field.append("Location")
                        if not currency and "Currency" not in mandatory_field:
                            mandatory_field.append("Currency")
                        if not prefix and "Prefix" not in mandatory_field:
                            mandatory_field.append("Prefix")

                        if mandatory_field:
                            break

                        exist_supplier = Supplier.objects.filter(
                                supplier_type=supplier_type,
                                product_type=product_type,
                                company_name=company_name,
                                location=location,
                                currency=currency,
                                contact_type=contact_type,
                                contact_person_1=contact_person_1,
                                prefix=prefix,
                            ).first()

                        if exist_supplier:
                            exist_suppliers.append(company_name)
                            continue

                        category_obj = Category.objects.filter(name=supplier_type, type="Supplier Category").first()
                        if not category_obj:
                            category_obj = Category.objects.create(name=supplier_type, type="Supplier Category")
                    
                        for prod_type in product_type:
                            obj, created = Category.objects.update_or_create(
                                        name=prod_type,
                                        parent_id=category_obj.id,
                                        type="Product Category",
                                        defaults={}  
                                    )

                        obj, created = SystemParameters.objects.update_or_create(
                                        system_parameter="Location",
                                        name=location,
                                        defaults={
                                            "created_by": request.user,
                                        }  
                                    )
                        
                        obj, created = SystemParameters.objects.update_or_create(
                                        system_parameter="Currency",
                                        name=currency,
                                        defaults={
                                            "created_by": request.user,
                                        }  
                                    )
                        
                        obj, created = SystemParameters.objects.update_or_create(
                                        system_parameter="Contact type",
                                        name=contact_type,
                                        defaults={
                                            "created_by": request.user,
                                        }  
                                    )

                        supplier_obj = Supplier.objects.create(
                            supplier_type=supplier_type,
                            product_type=product_type,
                            company_name=company_name,
                            location=location,
                            currency=currency,
                            prefix=prefix,
                            contact_type=contact_type,
                            contact_person_1=contact_person_1,
                            phone_1=phone_1,
                            contact_person_2=contact_person_2,
                            phone_2=phone_2,
                            email=email,
                            website=website,
                            remark=remark,
                            purchasing_comments=purchasing_comments,
                            created_by=request.user,
                            last_po_date=last_purchase_order.created_date if last_purchase_order else None,
                        )

                        if supplier_obj:
                            supplier_obj.supplier_id = f"S{supplier_obj.id:05}"
                            supplier_obj.save()
                    
                    if mandatory_field:
                        msg = "`" + ", ".join(mandatory_field) + "` Fields are mandatory. <div style='padding-top: 7px !important;'>Please add relevant data!</div>" if len(mandatory_field) > 1 else "`" + ", ".join(mandatory_field) + "` Field is mandatory. <div style='padding-top: 7px !important;'>Please add relevant data!</div>"
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")

                    if exist_suppliers:
                        msg = "`" + ", ".join(exist_suppliers) + "` suppliers are already exist." if len(exist_suppliers) > 1 else "`" + ", ".join(exist_suppliers) + "` supplier is already exist."
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")
                    # if supplier_obj:
                    #     supplier_objs = Supplier.objects.bulk_create(supplier_obj)

                return HttpResponse(json.dumps({"code": 1, "msg": "Success."}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")