from datetime import datetime, timedelta
from django.shortcuts import redirect, render
from apps.home.forms.customerform import CustomerForm
from apps.home.forms.addressform import AddressForm
from apps.home.model.customer import Customer, Customer_Files, Address
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.utils.translation import gettext_lazy as _
import sys, json, os, base64, traceback
from apps.home.model.order import Order
from apps.home.models import SystemParameters
from django.db import transaction
from django.db.models import Count, Sum, Min, Max
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.authentication.models import User
from apps.home.crud import utils, storage_backends, manager
from django.db.models import Q
import pandas as pd
from django.http import FileResponse
from django.conf import settings


@login_required(login_url="/login/")
def customerList(request):
    form = CustomerForm()
    customers_data = []
    daterange = ""
    try:
        utils.check_customer_activity()
        query = Q()
        from_date = request.GET["from_date"] if "from_date" in request.GET else ""
        to_date = request.GET["to_date"] if "to_date" in request.GET else ""

        if from_date and to_date:
            start_date = datetime.strptime(from_date, "%m/%d/%Y").strftime("%Y-%m-%d 00:00:00")
            end_date = datetime.strptime(to_date, "%m/%d/%Y").strftime("%Y-%m-%d 23:59:59")
            query.add(Q(created_date__range=(start_date, end_date)), query.connector)

        if request.user.role == "seller":
            query.add(Q(created_by_id=request.user.id), query.connector)

        customers = Customer.objects.filter(query).values(
            "id",
            "customer_id",
            "industry_type",
            "name",
            "english_name",
            "company_name",
            "company_english_name",
            "contact_person_1",
            "phone_number",
            "contact_person_2",
            "phone_number_2",
            "landline",
            "country",
            "district_in_hk",
            "prefix",
            "currency",
            "email",
            "source",
            "sale_person",
            "sale_person__first_name",
            "sale_person__last_name",
            "status",
            "delivery_comments",
            "customer_comments",
            "created_by__first_name",
            "created_by__last_name",
            "created_date",
            "accumlated_sales",
        ).order_by("-id")

        customer_ids = list(customers.values_list("id", flat=True))
        customer_wise_file = {}
        customer_files = Customer_Files.objects.filter(customer_id__in=customer_ids).values("customer_id", "file", "file_name")
        for cust_file in customer_files:
            if cust_file["customer_id"] not in customer_wise_file:
                customer_wise_file[cust_file["customer_id"]] = {"file_path": cust_file["file"], "file_name": cust_file["file_name"]}

        customer_wise_address = {}
        address_data = Address.objects.filter(customer_id__in=customer_ids).values("customer_id", "address_line", "address_2", "address_3")
        for address in address_data:
            customer_wise_address[int(address["customer_id"])] = {"main_address": address["address_line"], "address_2": address["address_2"], "address_3": address["address_3"]}

        order_data = Order.objects.filter(is_deleted=False).exclude(order_status__in=["cancelled", "rejected", "draft"]).values('customer_id').annotate(order_count=Count('id'), first_order_date=Min('created_date'), last_order_date=Max('created_date'))

        # customer_wise_accumlated_sales = {}
        # order_data_total_cost = Order.objects.filter(customer_id__in=customer_ids).values("id", "customer_id", "currency", "total_cost")
        # for od_cost in order_data_total_cost:
        #     total_cost = od_cost["total_cost"]
        #     if str(od_cost["currency"]).lower() != "hkd":
        #         converted_price = convert_currency(total_cost, od_cost["currency"], "HKD")
        #         if converted_price:
        #             total_cost = converted_price

        #     if od_cost["customer_id"] not in customer_wise_accumlated_sales:
        #         customer_wise_accumlated_sales[od_cost["customer_id"]] = float(total_cost)
        #     else:
        #         customer_wise_accumlated_sales[od_cost["customer_id"]] += total_cost

        for customer in customers:
            base64_with_prefix = ""
            if customer["id"] in customer_wise_file:
                file_path = str(customer_wise_file[customer["id"]]["file_path"])
                bucket_name = settings.MEDIA_BUCKET_NAME
                file_name = str(customer_wise_file[customer["id"]]["file_name"])
                customer_id = customer["id"]
                object_name = f"{customer_id}/{file_name}"
                base64_with_prefix = storage_backends.get_file(bucket_name, object_name)
                # if os.path.exists(file_path):
                #     with open(file_path, "rb") as file:
                #         image_data = file.read()
                #         base64_str = base64.b64encode(image_data).decode("utf-8")
                #         base64_with_prefix = "data:image/jpeg;base64," + base64_str 

            no_of_orders = 0
            # accumlated_sales = 0
            first_order_date = ""
            last_order_date = ""
            for order in order_data:
                if order["customer_id"] == customer["id"]:
                    no_of_orders = order["order_count"]
                    # accumlated_sales = order["total_cost"]
                    first_order_date = order["first_order_date"]
                    last_order_date = order["last_order_date"]
                    break

            sales_person = utils.get_user_full_name(customer["sale_person__first_name"], customer["sale_person__last_name"])

            customers_data.append({
                "id": customer["id"],
                "customer_id": customer["customer_id"],
                "customer_name": customer["name"],
                "customer_eng_name": customer["english_name"] if customer["english_name"] else "-",
                "company_name": customer["company_name"],
                "company_english_name": customer["company_english_name"] if customer["company_english_name"] else "-",
                "contact_person_1": customer["contact_person_1"],
                "phone_1": customer["phone_number"] if customer["phone_number"] else "-",
                "contact_person_2": customer["contact_person_2"] if customer["contact_person_2"] else "-",
                "phone_2": customer["phone_number_2"] if customer["phone_number_2"] else "-",
                "landline": customer["landline"] if customer["landline"] else "-",
                "district_in_hk": customer["district_in_hk"],
                "main_address": customer_wise_address[customer["id"]]["main_address"] if customer["id"] in customer_wise_address and customer_wise_address[customer["id"]]["main_address"] else "-",
                "address_2": customer_wise_address[customer["id"]]["address_2"] if customer["id"] in customer_wise_address and customer_wise_address[customer["id"]]["address_2"] else "-",
                "address_3": customer_wise_address[customer["id"]]["address_3"] if customer["id"] in customer_wise_address and customer_wise_address[customer["id"]]["address_3"] else "-",
                "delivery_comments": customer["delivery_comments"] if customer["delivery_comments"] else "-",
                "customer_comments": customer["customer_comments"] if customer["customer_comments"] else "-",
                "sales_person": sales_person if sales_person else "-",
                "no_of_orders": no_of_orders,
                "accumlated_sales": round(float(customer["accumlated_sales"]), 2) if customer["accumlated_sales"] else 0,
                "first_order_date": datetime.strptime(str(first_order_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if first_order_date else "-",
                "last_order_date": datetime.strptime(str(last_order_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if last_order_date else "-",
                "status": customer["status"],
                "created_date": datetime.strptime(str(customer["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "industry_type": customer["industry_type"],
                "source": customer["source"],
                "country": customer["country"],
                "prefix": customer["prefix"],
                "currency": customer["currency"],
                "email": customer["email"] if customer["email"] else "-",
                "name_card_file_name": customer_wise_file[customer["id"]]["file_name"] if customer["id"] in customer_wise_file else "-",
                "name_card_file_path": base64_with_prefix,
            })

        if from_date and to_date:
            daterange = from_date + " - " + to_date

        return render(request, 'home/customer-list.html', {"customers": customers_data, 'form': form, "role": request.user.role, "daterange": daterange})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/customer-list.html', {"customers": customers_data, 'form': form, "role": request.user.role, "daterange": daterange, "error_msg": str(e)})
    

@login_required(login_url="/login/")
def customer_list_export(request):
    customers_data = []
    try:
        query = Q()
        from_date = request.GET["from_date"] if "from_date" in request.GET else ""
        to_date = request.GET["to_date"] if "to_date" in request.GET else ""

        if from_date and to_date:
            start_date = datetime.strptime(from_date, "%m/%d/%Y").strftime("%Y-%m-%d 00:00:00")
            end_date = datetime.strptime(to_date, "%m/%d/%Y").strftime("%Y-%m-%d 23:59:59")
            query.add(Q(created_date__range=(start_date, end_date)), query.connector)

        if request.user.role == "seller":
            query.add(Q(created_by_id=request.user.id), query.connector)

        customers = Customer.objects.filter(query).values(
            "id",
            "customer_id",
            "industry_type",
            "name",
            "english_name",
            "company_name",
            "company_english_name",
            "contact_person_1",
            "phone_number",
            "contact_person_2",
            "phone_number_2",
            "landline",
            "country",
            "district_in_hk",
            "prefix",
            "currency",
            "email",
            "source",
            "sale_person",
            "sale_person__first_name",
            "sale_person__last_name",
            "status",
            "delivery_comments",
            "customer_comments",
            "created_by__first_name",
            "created_by__last_name",
            "created_date",
            "accumlated_sales",
        ).order_by("-id")

        customer_ids = list(customers.values_list("id", flat=True))
        customer_wise_file = {}
        customer_files = Customer_Files.objects.filter(customer_id__in=customer_ids).values("customer_id", "file", "file_name")
        for cust_file in customer_files:
            if cust_file["customer_id"] not in customer_wise_file:
                customer_wise_file[cust_file["customer_id"]] = {"file_path": cust_file["file"], "file_name": cust_file["file_name"]}

        customer_wise_address = {}
        address_data = Address.objects.filter(customer_id__in=customer_ids).values("customer_id", "address_line", "address_2", "address_3")
        for address in address_data:
            customer_wise_address[int(address["customer_id"])] = {"main_address": address["address_line"], "address_2": address["address_2"], "address_3": address["address_3"]}

        order_data = Order.objects.filter(is_deleted=False).exclude(order_status__in=["cancelled", "rejected", "draft"]).values('customer_id').annotate(order_count=Count('id'), first_order_date=Min('created_date'), last_order_date=Max('created_date'))

        for customer in customers:
            no_of_orders = 0
            first_order_date = ""
            last_order_date = ""
            for order in order_data:
                if order["customer_id"] == customer["id"]:
                    no_of_orders = order["order_count"]
                    first_order_date = order["first_order_date"]
                    last_order_date = order["last_order_date"]
                    break

            sales_person = utils.get_user_full_name(customer["sale_person__first_name"], customer["sale_person__last_name"])

            customers_data.append({
                "Created Date": datetime.strptime(str(customer["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "Customer Name": customer["name"],
                "Customer English Name": customer["english_name"] if customer["english_name"] else "",
                "Company Name": customer["company_name"],
                "Company English Name": customer["company_english_name"] if customer["company_english_name"] else "",
                "Contact Person 1": customer["contact_person_1"],
                "Phone 1": customer["phone_number"] if customer["phone_number"] else "",
                "Contact Person 2": customer["contact_person_2"] if customer["contact_person_2"] else "",
                "Phone 2": customer["phone_number_2"] if customer["phone_number_2"] else "",
                "Landline": customer["landline"] if customer["landline"] else "",
                "18 District in HK": customer["district_in_hk"],
                "Main Address": customer_wise_address[customer["id"]]["main_address"] if customer["id"] in customer_wise_address and customer_wise_address[customer["id"]]["main_address"] else "",
                "Address 2": customer_wise_address[customer["id"]]["address_2"] if customer["id"] in customer_wise_address and customer_wise_address[customer["id"]]["address_2"] else "",
                "Address 3": customer_wise_address[customer["id"]]["address_3"] if customer["id"] in customer_wise_address and customer_wise_address[customer["id"]]["address_3"] else "",
                "Delivery Comments": customer["delivery_comments"] if customer["delivery_comments"] else "",
                "Customer Comments": customer["customer_comments"] if customer["customer_comments"] else "",
                "Salesperson": sales_person if sales_person else "",
                "No. of Orders": no_of_orders,
                "Accumulated Sales (HKD)": round(float(customer["accumlated_sales"]), 2) if customer["accumlated_sales"] else 0,
                "First Order Date": datetime.strptime(str(first_order_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if first_order_date else "",
                "Last Order Date": datetime.strptime(str(last_order_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if last_order_date else "",
                "Status": customer["status"],
                "Customer ID": customer["customer_id"],
                "Industry Type": customer["industry_type"],
                "Source": customer["source"],
                "Country/District": customer["country"],
                "Prefix": customer["prefix"],
                "Currency": customer["currency"],
                "Email": customer["email"] if customer["email"] else "",
                "Name Card Preview": customer_wise_file[customer["id"]]["file_name"] if customer["id"] in customer_wise_file else "",
            })

        df = pd.DataFrame(customers_data)

        now = datetime.now().strftime("%d%m%Y")
        file_path = 'media/temp/customers/' + str(request.user.id) + "/"
        file_name = "customers_" + str(now) + ".xlsx"
        full_file_path = file_path + file_name
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        df.to_excel(full_file_path, index=False)        

        response = FileResponse(open(full_file_path, 'rb'), content_type='text/xlsx')
        response['Content-Disposition'] = f'attachment; filename=' + file_name
        return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/customer-list.html', {"role": request.user.role, "error_msg": str(e)})


# @login_required(login_url="/login/")
# def customerCreate(request):
#     msg = ''
#     form = CustomerForm()
    
#     if request.method == "POST":
#         form = CustomerForm(request.POST)

#         if form.is_valid():

#             try:
#                 last_customer = Customer.objects.order_by("-id").first()
#                 obj=form.save()
#                 if last_customer and last_customer.customer_id:
#                     obj.customer_id = int(last_customer.customer_id) + 1
#                 else:
#                     obj.customer_id = 200001
#                 obj.save()
#                 messages.success(request,  _("Customer added successfully"))
#                 return redirect('address', obj.id)
#             except Exception as e:
#                 raise e
#         else:
#             messages.error(request, form.errors)
        
#     return render(request, 'home/customer.html', {"msg": msg, 'form': form})


@login_required(login_url="/login/")
def customerCreate(request):
    industry_types = []
    countries = []
    districts_in_hk = []
    currencies = []
    sources = []
    prefixes = []
    sales_person_data = []
    created_date = datetime.now().strftime("%Y-%m-%d")
    try:
        system_parameters_data = SystemParameters.objects.filter(is_deleted=False).all()
        for system_param in system_parameters_data:
            if str(system_param.system_parameter).lower() == "industry type":
                industry_types = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "country/district":
                countries = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "currency":
                currencies = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "district in hk":
                districts_in_hk = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "source":
                sources = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "prefix":
                prefixes = str(system_param.name).split(", ")
            if str(system_param.system_parameter).lower() == "sales person":
                sales_person_ids = str(system_param.name).split(", ")
                sales_persons = User.objects.filter(is_active=True, id__in=sales_person_ids).values("id", "username", "first_name", "last_name").order_by('-id')
                for sale_person in sales_persons:
                    first_name = sale_person["first_name"]
                    last_name = sale_person["last_name"]
                    sales_person = utils.get_user_full_name(first_name, last_name)
                    
                    sales_person_data.append({
                        "id": sale_person["id"],
                        "full_name": sales_person if sales_person else "",
                    })

        if request.method == "POST":
            with transaction.atomic():
                customer_name = request.POST.get("customer_name")
                customer_eng_name = request.POST.get("customer_eng_name")
                company_name = request.POST.get("company_name")
                phone_1 = request.POST.get("phone_1")
                prefix = request.POST.get("prefix")
                email = request.POST.get("email")
                salesperson = request.POST.get("salesperson")
                company_eng_name = request.POST.get("company_eng_name")
                contact_person_2 = request.POST.get("contact_person_2")
                contact_person_2_chinese = request.POST.get("contact_person_2_chinese")
                country = request.POST.get("country")
                landline = request.POST.get("landline")
                currency = request.POST.get("currency")
                source = request.POST.get("source")
                name_card_file = request.FILES.get('name_card_file')
                status = request.POST.get("status")
                industry_type = request.POST.get("industry_type")
                contact_person_1 = request.POST.get("contact_person_1")
                contact_person_1_chinese = request.POST.get("contact_person_1_chinese")
                phone_2 = request.POST.get("phone_2")
                district_in_hk = request.POST.get("district_in_hk")
                main_address = request.POST.get("main_address")
                main_address_chinese = request.POST.get("main_address_chinese")
                address_2 = request.POST.get("address_2")
                address_2_chinese = request.POST.get("address_2_chinese")
                address_3 = request.POST.get("address_3")
                address_3_chinese = request.POST.get("address_3_chinese")
                delivery_comments = request.POST.get("delivery_comments")
                customer_comments = request.POST.get("customer_comments")
                button_clicked = request.POST.get("button_clicked")

                exist_customer = Customer.objects.filter(
                            name=customer_name,
                            industry_type=industry_type,
                            company_name=company_name,
                            company_english_name=company_eng_name,
                            district_in_hk=district_in_hk,
                            country=country,
                            prefix=prefix,
                            currency=currency,
                            contact_person_1=contact_person_1,
                            contact_person_1_chinese=contact_person_1_chinese,
                            source=source,
                            sale_person=salesperson,
                            ).first()

                if exist_customer:
                    return render(request, 'home/customer.html', {
                                "industry_types": industry_types, 
                                "countries": countries, 
                                "currency": currencies,
                                "districts_in_hk": districts_in_hk,
                                "sources": sources,
                                "prefixes": prefixes,
                                "sales_person_data": sales_person_data,
                                "created_date": created_date,
                                "role": request.user.role,
                                "logged_in_user_id": request.user.id,
                                "error_msg": "Customer is already exist."
                                })
                
                customer_obj = Customer.objects.create(
                    industry_type=industry_type,
                    name=customer_name,
                    english_name=customer_eng_name,
                    company_name=company_name,
                    company_english_name=company_eng_name,
                    contact_person_1=contact_person_1,
                    contact_person_1_chinese=contact_person_1_chinese,
                    phone_number=phone_1,
                    contact_person_2=contact_person_2,
                    contact_person_2_chinese=contact_person_2_chinese,
                    phone_number_2=phone_2,
                    landline=landline,
                    country=country,
                    district_in_hk=district_in_hk,
                    prefix=prefix,
                    currency=currency,
                    email=email,
                    source=source,
                    sale_person_id=salesperson,
                    status="draft" if button_clicked and button_clicked == "saveBtn" else "potential customer",
                    delivery_comments=delivery_comments,
                    customer_comments=customer_comments,
                    created_by=request.user,
                )

                if customer_obj:
                    customer_obj.customer_id = f"C{customer_obj.id:05}"
                    customer_obj.save()
                    Address.objects.create(address_line=main_address, address_line_chinese=main_address_chinese, address_2=address_2, address_2_chinese=address_2_chinese, address_3=address_3, address_3_chinese=address_3_chinese, customer_id=customer_obj.id)
                    if name_card_file:
                        customer_file_obj = Customer_Files.objects.create(customer_id=customer_obj.id, file=name_card_file, file_name=name_card_file.name)
                        customer_file = Customer_Files.objects.filter(id=customer_file_obj.id).values("file", "file_name").first()
                        file_path = customer_file["file"]
                        file_name = customer_file["file_name"]
                        bucket_name = settings.MEDIA_BUCKET_NAME
                        object_name = f"{customer_obj.id}/{file_name}"
                        is_bucket = storage_backends.create_bucket(bucket_name)
                        if is_bucket:
                            is_file_upload = storage_backends.upload_file(file_path, bucket_name, object_name)

                return redirect("customer-list")
        else:
            return render(request, 'home/customer.html', {
                "industry_types": industry_types, 
                "countries": countries,
                "currency": currencies,
                "districts_in_hk": districts_in_hk,
                "sources": sources,
                "prefixes": prefixes,
                "sales_person_data": sales_person_data,
                "created_date": created_date,
                "role": request.user.role,
                "logged_in_user_id": request.user.id,
                })
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/customer.html', {
                                    "industry_types": industry_types, 
                                    "countries": countries, 
                                    "currency": currencies,
                                    "districts_in_hk": districts_in_hk,
                                    "sources": sources,
                                    "prefixes": prefixes,
                                    "sales_person_data": sales_person_data,
                                    "created_date": created_date,
                                    "role": request.user.role,
                                    "logged_in_user_id": request.user.id,
                                    "error_msg": str(e),
                                    })


@login_required(login_url="/login/")
def customerUpdate(request, id):
    try:
        exist_customer = Customer.objects.filter(id=id).first()
        if exist_customer:
            if request.method == "POST":
                with transaction.atomic():
                    customer_name = request.POST.get("customer_name")
                    customer_eng_name = request.POST.get("customer_eng_name")
                    company_name = request.POST.get("company_name")
                    phone_1 = request.POST.get("phone_1")
                    prefix = request.POST.get("prefix")
                    email = request.POST.get("email")
                    salesperson = request.POST.get("salesperson")
                    company_eng_name = request.POST.get("company_eng_name")
                    contact_person_2 = request.POST.get("contact_person_2")
                    contact_person_2_chinese = request.POST.get("contact_person_2_chinese")
                    country = request.POST.get("country")
                    landline = request.POST.get("landline")
                    currency = request.POST.get("currency")
                    source = request.POST.get("source")
                    name_card_file = request.FILES.get('name_card_file')
                    status = request.POST.get("status")
                    industry_type = request.POST.get("industry_type")
                    contact_person_1 = request.POST.get("contact_person_1")
                    contact_person_1_chinese = request.POST.get("contact_person_1_chinese")
                    phone_2 = request.POST.get("phone_2")
                    district_in_hk = request.POST.get("district_in_hk")
                    main_address = request.POST.get("main_address")
                    main_address_chinese = request.POST.get("main_address_chinese")
                    address_2 = request.POST.get("address_2")
                    address_2_chinese = request.POST.get("address_2_chinese")
                    address_3 = request.POST.get("address_3")
                    address_3_chinese = request.POST.get("address_3_chinese")
                    delivery_comments = request.POST.get("delivery_comments")
                    customer_comments = request.POST.get("customer_comments")
                    button_clicked = request.POST.get("button_clicked")

                    status = str(status).lower()
                    if str(status).lower() == "draft" and button_clicked == "saveBtn":
                        status = "draft"
                    elif str(status).lower() == "draft" and button_clicked == "submitBtn":
                        status = "potential customer"

                    customer_obj = Customer.objects.filter(id=id).update(
                        industry_type=industry_type,
                        name=customer_name,
                        english_name=customer_eng_name,
                        company_name=company_name,
                        company_english_name=company_eng_name,
                        contact_person_1=contact_person_1,
                        contact_person_1_chinese=contact_person_1_chinese,
                        phone_number=phone_1,
                        contact_person_2=contact_person_2,
                        contact_person_2_chinese=contact_person_2_chinese,
                        phone_number_2=phone_2,
                        landline=landline,
                        country=country,
                        district_in_hk=district_in_hk,
                        prefix=prefix,
                        currency=currency,
                        email=email,
                        source=source,
                        sale_person_id=salesperson,
                        status=status,
                        delivery_comments=delivery_comments,
                        customer_comments=customer_comments,
                    )

                    Address.objects.filter(customer_id=id).update(address_line=main_address, address_line_chinese=main_address_chinese, address_2=address_2, address_2_chinese=address_2_chinese, address_3=address_3, address_3_chinese=address_3_chinese)

                    if name_card_file:
                        bucket_name = settings.MEDIA_BUCKET_NAME
                        folder_name = id  # This is the "folder" name within the bucket
                        file_path = ""
                        file_name = ""
                        customer_file_exist = Customer_Files.objects.filter(customer_id=id).first()
                        if customer_file_exist:
                            old_file_name = str(customer_file_exist.file_name)
                            old_file_path = str(customer_file_exist.file)
                            customer_file_exist.file = name_card_file
                            customer_file_exist.file_name = name_card_file.name
                            customer_file_exist.save()
                            
                            file_path = str(customer_file_exist.file)
                            file_name = str(customer_file_exist.file_name)
                            object_name = f"{folder_name}/{old_file_name}"
                            is_deleted = storage_backends.delete_file(bucket_name, object_name)
                        else:
                            customer_file_obj = Customer_Files.objects.create(customer_id=id, file=name_card_file, file_name=name_card_file.name)
                            customer_file = Customer_Files.objects.filter(id=customer_file_obj.id).values("file", "file_name").first()
                            file_path = customer_file["file"]
                            file_name = customer_file["file_name"] 

                        if file_path and file_name:
                            object_name = f"{folder_name}/{file_name}"
                            is_bucket = storage_backends.create_bucket(bucket_name)
                            if is_bucket:
                                is_file_upload = storage_backends.upload_file(file_path, bucket_name, object_name)

                    return redirect("customer-list")
            else:
                name_card_data = Customer_Files.objects.filter(customer_id=exist_customer.id).first()
                address_data = Address.objects.filter(customer_id=id).values("customer_id", "address_line", "address_line_chinese", "address_2", "address_2_chinese", "address_3", "address_3_chinese").first()

                industry_types = []
                countries = []
                districts_in_hk = []
                currencies = []
                sources = []
                prefixes = []
                sales_person_data = []
                system_parameters_data = SystemParameters.objects.filter(is_deleted=False).all()
                for system_param in system_parameters_data:
                    if str(system_param.system_parameter).lower() == "industry type":
                        industry_types = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "country/district":
                        countries = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "currency":
                        currencies = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "district in hk":
                        districts_in_hk = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "source":
                        sources = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "prefix":
                        prefixes = str(system_param.name).split(", ")
                    if str(system_param.system_parameter).lower() == "sales person":
                        sales_person_ids = str(system_param.name).split(", ")
                        sales_persons = User.objects.filter(is_active=True, id__in=sales_person_ids).values("id", "username", "first_name", "last_name").order_by('-id')
                        for sale_person in sales_persons:
                            first_name = sale_person["first_name"]
                            last_name = sale_person["last_name"]
                            sales_person = utils.get_user_full_name(first_name, last_name)
                            
                            sales_person_data.append({
                                "id": sale_person["id"],
                                "full_name": sales_person if sales_person else "",
                            })

                order_data = list(Order.objects.filter(customer_id=id, is_deleted=False).exclude(order_status__in=["cancelled", "rejected", "draft"]).values('customer_id').annotate(order_count=Count('id'), total_cost=Sum('total_cost'), first_order_date=Min('created_date'), last_order_date=Max('created_date')))
                
                # accumlated_sales = 0
                # order_data_total_cost = Order.objects.filter(customer_id=id).values("id", "customer_id", "currency", "total_cost")
                # for od_cost in order_data_total_cost:
                #     total_cost = od_cost["total_cost"]
                #     if str(od_cost["currency"]).lower() != "hkd":
                #         converted_price = convert_currency(total_cost, od_cost["currency"], "HKD")
                #         if converted_price:
                #             total_cost = converted_price

                #     accumlated_sales += float(total_cost)

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

                customer_data = {
                    "id": exist_customer.id,
                    "customer_id": exist_customer.customer_id,
                    "customer_name": exist_customer.name,
                    "customer_eng_name": exist_customer.english_name if exist_customer.english_name else "",
                    "company_name": exist_customer.company_name,
                    "company_english_name": exist_customer.company_english_name if exist_customer.company_english_name else "",
                    "contact_person_1": exist_customer.contact_person_1,
                    "contact_person_1_chinese": exist_customer.contact_person_1_chinese,
                    "phone_1": exist_customer.phone_number if exist_customer.phone_number else "",
                    "contact_person_2": exist_customer.contact_person_2 if exist_customer.contact_person_2 else "",
                    "contact_person_2_chinese": exist_customer.contact_person_2_chinese if exist_customer.contact_person_2_chinese else "",
                    "phone_2": exist_customer.phone_number_2 if exist_customer.phone_number_2 else "",
                    "landline": exist_customer.landline if exist_customer.landline else "",
                    "district_in_hk": exist_customer.district_in_hk,
                    "main_address": address_data["address_line"] if address_data and address_data["address_line"] else "",
                    "main_address_chinese": address_data["address_line_chinese"] if address_data and address_data["address_line_chinese"] else "",
                    "address_2": address_data["address_2"] if address_data and address_data["address_2"] else "",
                    "address_2_chinese": address_data["address_2_chinese"] if address_data and address_data["address_2_chinese"] else "",
                    "address_3": address_data["address_3"] if address_data and address_data["address_3"] else "",
                    "address_3_chinese": address_data["address_3_chinese"] if address_data and address_data["address_3_chinese"] else "",
                    "delivery_comments": exist_customer.delivery_comments if exist_customer.delivery_comments else "",
                    "customer_comments": exist_customer.customer_comments if exist_customer.customer_comments else "",
                    "sales_person": exist_customer.sale_person_id,
                    "no_of_orders": order_data[0]["order_count"] if order_data and order_data[0]["order_count"] else 0,
                    "accumlated_sales": round(float(exist_customer.accumlated_sales), 2) if exist_customer.accumlated_sales else 0,
                    "first_order_date": datetime.strptime(str(order_data[0]["first_order_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if order_data and order_data[0]["first_order_date"] else "",
                    "last_order_date": datetime.strptime(str(order_data[0]["last_order_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if order_data and order_data[0]["last_order_date"] else "",
                    "status": exist_customer.status,
                    "created_date": datetime.strptime(str(exist_customer.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                    "industry_type": exist_customer.industry_type,
                    "source": exist_customer.source,
                    "country": exist_customer.country,
                    "prefix": exist_customer.prefix,
                    "currency": exist_customer.currency,
                    "email": exist_customer.email if exist_customer.email else "",
                    "name_card_file_name": name_card_data.file_name if name_card_data and name_card_data.file_name else "",
                    "name_card_file_path": base64_with_prefix,
                }

                return render(request, 'home/customer_details.html', {
                    "customer_data": customer_data,
                    "role": request.user.role,
                    "industry_types": industry_types,
                    "countries": countries,
                    "districts_in_hk": districts_in_hk,
                    "currency": currencies,
                    "sources": sources,
                    "prefixes": prefixes,
                    "sales_person_data": sales_person_data,
                    })
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


# @login_required(login_url="/login/")
# def customerUpdate(request, id):
#     msg = ''
#     customer = Customer.objects.filter(id=id)
#     if not customer:
#         msg = _("customer not found")
#     else:
#         customer = customer.first()
#         form = CustomerForm(instance=customer)
        
#         if request.method == "POST":
#             form = CustomerForm(request.POST, instance=customer)
#             if form.is_valid():
#                 try:
#                     form.save()

#                     msg = _("customer updated successfully")
#                 except Exception as e:
#                     raise e
#             else:
#                 msg = _("form is invalid")
#     return render(request, 'home/customer.html', {"msg": msg, 'form': form})


@login_required(login_url="/login/")
def customerGet(request, id):
    msg =''
    customer = Customer.objects.get(id=id)
    if not customer:
        msg = _("customer not found")
    addresses = customer.addresses.all()
    # customer=customer.__dict__
    # customer.pop("_state")
    # customer.pop("created_date")    
    # customer.pop("updated_date") 
    # customer = {key.replace("_"," "):customer[key] for key in customer}
    

    return render(request, 'home/customer-detail.html', {"msg": msg, "customer":customer, "addresses":addresses})
@login_required(login_url="/login/")
def customerDelete(request, id):
    msg =''
    try:
        
        customer = Customer.objects.filter(id=id)
        orders = Order.objects.filter(customer=customer)
        customer.delete()
        orders.delete()
        msg=_("customer deleted successfully")
    except Exception as e:
        pass
    customers = Customer.objects.all()
    return render(request, 'home/customer-list.html', {"msg": msg, "customers":customers})


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def customer_delete(request):
    try:
        if request.method == "POST":
            customer_id = request.POST.get("customer_id")
            order_exist = list(Order.objects.filter(customer_id=customer_id).values_list("order_id", flat=True))
            if order_exist:
                msg = "Cannot delete this customer because it is used in the Order `<b>" + ", ".join(order_exist) + "</b>`."
                if len(order_exist) > 1:
                    msg = "Cannot delete this customer because it is used in the Orders `<b>" + ", ".join(order_exist) + "</b>`."
                return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")
            customer_name_card = Customer_Files.objects.filter(customer_id=customer_id).values("file", "file_name").first()
            Customer.objects.filter(id=customer_id).delete()
            if customer_name_card:
                utils.remove_file(customer_name_card["file"].replace("/" + os.path.basename(str(customer_name_card["file"])), ""))
                bucket_name = settings.MEDIA_BUCKET_NAME
                file_name = str(customer_name_card["file_name"])
                object_name = f"{customer_id}/{file_name}"

                is_deleted = storage_backends.delete_file(bucket_name, object_name)

            return HttpResponse(json.dumps({"code": 1, "msg": "Success!"}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json") 


@login_required(login_url="/login/")
def download_customer_name_card(request, id):
    try:
        name_card = Customer_Files.objects.filter(customer_id=id).values("file", "file_name").first()
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
            
            # with open(file_path, 'rb') as file:   
            #     response = HttpResponse(file.read())
            #     response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(str(file_path))
            #     return response
        else:
            return HttpResponse(json.dumps({"code": 0, "msg": "File not found."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")
    

@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def remove_customer_name_card(request):
    try:
        customer_id = request.POST.get("customer_id")
        name_card = Customer_Files.objects.filter(customer_id=customer_id).first()
        if name_card:
            file_path = str(name_card.file)
            file_path = file_path.replace("/" + os.path.basename(str(file_path)), "")
            bucket_name = settings.MEDIA_BUCKET_NAME
            file_name = str(name_card.file_name)
            object_name = f"{customer_id}/{file_name}"

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
def customer_import_samplefile(request):
    try:
        full_file_path = 'sample_files/import_customers_sample_file.xlsx'
        response = utils.download_samplefile(full_file_path, "import_customers_sample_file.xlsx")
        if response:
            return response
        return render(request, 'home/customer-list.html', {"error_msg": "Sample file not found."})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/customer-list.html', {"error_msg": str(e)})


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def customers_import(request):
    try:
        if request.method == "POST":
            import_customer_file = request.FILES.get("import_customer_file")
            if import_customer_file:
                with transaction.atomic():
                    xlsx_df = pd.read_excel(import_customer_file)
                    xlsx_df = xlsx_df.map(lambda x: None if pd.isna(x) or x == '' else x)
                    customers_dict = xlsx_df.to_dict(orient='records')
                    mandatory_field = []

                    exist_customers = []
                    for customer in customers_dict:
                        customer_name = customer["Customer Name"] if "Customer Name" in customer and customer["Customer Name"] else None
                        customer_english_name = customer["Customer English Name"] if "Customer English Name" in customer and customer["Customer English Name"] else None
                        company_name = customer["Company Name"] if "Company Name" in customer and customer["Company Name"] else None
                        company_english_name = customer["Company English Name"] if "Company English Name" in customer and customer["Company English Name"] else None
                        contact_person_1 = customer["Contact Person 1 English"] if "Contact Person 1 English" in customer and customer["Contact Person 1 English"] else None
                        contact_person_1_chinese = customer["Contact Person 1 Chinese"] if "Contact Person 1 Chinese" in customer and customer["Contact Person 1 Chinese"] else None
                        phone_1 = customer["Phone 1"] if "Phone 1" in customer and customer["Phone 1"] else None
                        contact_person_2 = customer["Contact Person 2 English"] if "Contact Person 2 English" in customer and customer["Contact Person 2 English"] else None
                        contact_person_2_chinese = customer["Contact Person 2 Chinese"] if "Contact Person 2 Chinese" in customer and customer["Contact Person 2 Chinese"] else None
                        phone_2 = customer["Phone 2"] if "Phone 2" in customer and customer["Phone 2"] else None
                        landline = customer["Landline"] if "Landline" in customer and customer["Landline"] else None
                        district_in_hk = customer["18 District in HK"] if "18 District in HK" in customer and customer["18 District in HK"] else None
                        main_address = customer["Main Address English"] if "Main Address English" in customer and customer["Main Address English"] else None
                        main_address_chinese = customer["Main Address Chinese"] if "Main Address Chinese" in customer and customer["Main Address Chinese"] else None
                        address_2 = customer["Address 2 English"] if "Address 2 English" in customer and customer["Address 2 English"] else None
                        address_2_chinese = customer["Address 2 Chinese"] if "Address 2 Chinese" in customer and customer["Address 2 Chinese"] else None
                        address_3 = customer["Address 3 English"] if "Address 3 English" in customer and customer["Address 3 English"] else None
                        address_3_chinese = customer["Address 3 Chinese"] if "Address 3 Chinese" in customer and customer["Address 3 Chinese"] else None
                        delivery_comments = customer["Delivery Comments"] if "Delivery Comments" in customer and customer["Delivery Comments"] else None
                        customer_comments = customer["Customer Comments"] if "Customer Comments" in customer and customer["Customer Comments"] else None
                        industry_type = customer["Industry Type"] if "Industry Type" in customer and customer["Industry Type"] else None
                        source = customer["Source"] if "Source" in customer and customer["Source"] else None
                        country = customer["Country/District"] if "Country/District" in customer and customer["Country/District"] else None
                        prefix = str(customer["Prefix"]) if "Prefix" in customer and customer["Prefix"] else None
                        prefix = "+" + str(prefix) if prefix and "+" not in str(prefix) else prefix
                        currency = customer["Currency"] if "Currency" in customer and customer["Currency"] else None
                        email = customer["Email"] if "Email" in customer and customer["Email"] else None

                        if not customer_name and "Customer Name" not in mandatory_field:
                            mandatory_field.append("Customer Name")
                        if not company_name and "Company Name" not in mandatory_field:
                            mandatory_field.append("Company Name")
                        if not contact_person_1 and "Contact Person 1 English" not in mandatory_field:
                            mandatory_field.append("Contact Person 1 English")
                        if not contact_person_1_chinese and "Contact Person 1 Chinese" not in mandatory_field:
                            mandatory_field.append("Contact Person 1 Chinese")
                        if not district_in_hk and "18 District in HK" not in mandatory_field:
                            mandatory_field.append("18 District in HK")
                        if not country and "Country/District" not in mandatory_field:
                            mandatory_field.append("Country/District")
                        if not main_address and "Main Address English" not in mandatory_field:
                            mandatory_field.append("Main Address English")
                        if not main_address_chinese and "Main Address Chinese" not in mandatory_field:
                            mandatory_field.append("Main Address Chinese")
                        if not prefix and "Prefix" not in mandatory_field:
                            mandatory_field.append("Prefix")
                        if not currency and "Currency" not in mandatory_field:
                            mandatory_field.append("Currency")
                        if not source and "Source" not in mandatory_field:
                            mandatory_field.append("Source")
                        if not industry_type and "Industry Type" not in mandatory_field:
                            mandatory_field.append("Industry Type")

                        if mandatory_field:
                            break

                        exist_customer = Customer.objects.filter(
                                name=customer_name,
                                company_name=company_name,
                                contact_person_1=contact_person_1,
                                contact_person_1_chinese=contact_person_1_chinese,
                                district_in_hk=district_in_hk,
                                country=country,
                                currency=currency,
                                source=source,
                                prefix=prefix,
                            ).first()

                        if exist_customer:
                            exist_customers.append(customer_name)
                            continue

                        sys_params = SystemParameters.objects.filter(system_parameter__in=["Industry Type", "District in HK", "Country/District", "Prefix", "Currency", "Source"])
                        for sys_param in sys_params:
                            if industry_type and sys_param.system_parameter == "Industry Type" and industry_type.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + industry_type.capitalize()
                            if prefix and sys_param.system_parameter == "Prefix" and prefix not in sys_param.name:
                                sys_param.name += ", " + prefix
                            if currency and sys_param.system_parameter == "Currency" and currency.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + currency.upper()
                            if country and sys_param.system_parameter == "Country/District" and country.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + country.capitalize()
                            if source and sys_param.system_parameter == "Source" and source.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + source.capitalize()
                            if district_in_hk and sys_param.system_parameter == "District in HK" and district_in_hk.lower() not in (sys_param.name).lower():
                                sys_param.name += ", " + district_in_hk.capitalize()
                            sys_param.save()

                        customer_obj = Customer.objects.create(
                            industry_type=industry_type,
                            name=customer_name,
                            english_name=customer_english_name,
                            company_name=company_name,
                            company_english_name=company_english_name,
                            contact_person_1=contact_person_1,
                            contact_person_1_chinese=contact_person_1_chinese,
                            phone_number=phone_1,
                            contact_person_2=contact_person_2,
                            contact_person_2_chinese=contact_person_2_chinese,
                            phone_number_2=phone_2,
                            landline=landline,
                            country=country,
                            district_in_hk=district_in_hk,
                            prefix=prefix,
                            currency=currency.upper(),
                            email=email,
                            source=source,
                            status="potential customer",
                            delivery_comments=delivery_comments,
                            customer_comments=customer_comments,
                            created_by=request.user,
                        )

                        if customer_obj:
                            customer_obj.customer_id = f"C{customer_obj.id:05}"
                            customer_obj.save()
                            Address.objects.create(address_line=main_address, address_line_chinese=main_address_chinese, address_2=address_2, address_2_chinese=address_2_chinese, address_3=address_3, address_3_chinese=address_3_chinese, customer_id=customer_obj.id)
                    
                    if mandatory_field:
                        msg = "`" + ", ".join(mandatory_field) + "` fields are mandatory. <div style='padding-top: 7px !important;'>Please add relevant data!</div>" if len(mandatory_field) > 1 else "`" + ", ".join(mandatory_field) + "` field is mandatory. <div style='padding-top: 7px !important;'>Please add relevant data!</div>"
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")

                    if exist_customers:
                        msg = "`" + ", ".join(exist_customers) + "` customers are already exist." if len(exist_customers) > 1 else "`" + ", ".join(exist_customers) + "` customer is already exist."
                        return HttpResponse(json.dumps({"code": 0, "msg": msg}), content_type="json")

                return HttpResponse(json.dumps({"code": 1, "msg": "Success."}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")