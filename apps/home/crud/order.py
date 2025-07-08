import json
from django.views import View
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import transaction
from datetime import datetime, timedelta, date
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.home.forms.orderconfirmationform import OrderConfirmationForm
from apps.home.model.customer import Customer, Address
from apps.home.models import Product, Orderitems, Order, Inventory, Voucher
from apps.home.forms.orderform import orderForm
from apps.home.forms.customerform import CustomerForm, CustomerSmallForm
from django.core.serializers import serialize
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
import os, sys, traceback, base64
import pandas as pd
from django.http import FileResponse
from forex_python.converter import CurrencyRates
from apps.authentication.models import User, Permissions
from apps.home.model.order import Order_notification
from retry import retry
from apps.home.models import SystemParameters
from apps.home.crud import utils, manager, storage_backends
from django.template.loader import render_to_string
from weasyprint import HTML
from apps.home.model.customer import Customer_Files
from django.conf import settings


@login_required(login_url="/login/")
def orderList(request):
    data = []
    daterange = ""
    try:
        utils.check_customer_activity()
        # start = request.GET.get('start')
        # end = request.GET.get('length')
        query = Q()
        from_date = request.GET["from_date"] if "from_date" in request.GET else ""
        to_date = request.GET["to_date"] if "to_date" in request.GET else ""

        if from_date and to_date:
            start_date = datetime.strptime(from_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            end_date = datetime.strptime(to_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            query.add(Q(date__range=(start_date, end_date)), query.connector)

        if request.user.role == "seller":
            query.add(Q(customer__sale_person_id=request.user.id), query.connector)

        query.add(Q(is_deleted=False), query.connector)
        query.add(Q(is_approve=True), query.connector)
        query.add(~Q(order_status__in=["cancelled", "rejected"]), query.connector)

        orders = Order.objects.filter(query).order_by("-id")

        for order in orders:
            sales_person = "-"
            if order.customer.sale_person:
                first_name = order.customer.sale_person.first_name
                last_name = order.customer.sale_person.last_name
                sales_person = utils.get_user_full_name(first_name, last_name)

            order_items = order.orderitems.all()
            for order_item in order_items:
                data.append({
                    "id": order.id,
                    "created_on": datetime.strptime(str(order.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                    "date": str(order.date) if order.date else '-',
                    "customer__company_name": order.customer.company_name if order.customer.company_name else "-",
                    "invoice_id": order.order_id,
                    "customer__phone_number": order.customer.phone_number if order.customer.phone_number else "-",
                    "product_id": order_item.product.product_id if order_item.product.product_id else "-",
                    "product_chinese_name": order_item.product.product_chinese_name if order_item.product.product_chinese_name else "-",
                    "ramarks": order_item.remarks if order_item.remarks else "-",
                    "quantity": order_item.quantity if order_item.quantity else "-",
                    "currency": order.currency if order.currency else "-",
                    "unit_price": str(order_item.selling_price) if order_item.selling_price else "-",
                    "total_price": str(order_item.total_cost) if order_item.total_cost else "-",
                    "total_cost": str(order.total_cost) if order.total_cost else "-",
                    "payment_method": order.payment_method if order.payment_method else "-",
                    "delivery_date": str(order.delivery_date) if order.delivery_date else "-",
                    "order_status": str(order.order_status).capitalize() if order.order_status else "-",
                    "sales_person": sales_person,
                    "type": order.type,
                    "is_approve": order.is_approve,
                })

        response = {
            # 'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': orders.count(),
            # 'recordsFiltered': paginator.count,
            'data': data,
            'code': 1,
        }

        if from_date and to_date:
            daterange = from_date + " - " + to_date

        return render(request, 'home/order-list.html', {"order_data": data, "daterange": daterange, "role": request.user.role})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/order-list.html', {"order_data": data, "daterange": daterange, "role": request.user.role, "error_msg": str(e)})


@login_required(login_url="/login/")
def order_approval_list(request):
    data = []
    daterange = ""
    try:
        query = Q()
        from_date = request.GET["from_date"] if "from_date" in request.GET else ""
        to_date = request.GET["to_date"] if "to_date" in request.GET else ""

        if from_date and to_date:
            start_date = datetime.strptime(from_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            end_date = datetime.strptime(to_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            query.add(Q(date__range=(start_date, end_date)), query.connector)

        if request.user.role == "seller":
            query.add(Q(user_id=request.user.id), query.connector)

        query.add(Q(is_approve=False), query.connector)
        query.add(Q(is_deleted=False), query.connector)

        orders = Order.objects.filter(query).order_by("-id")

        for order in orders:
            sales_person = "-"
            if order.customer.sale_person:
                first_name = order.customer.sale_person.first_name
                last_name = order.customer.sale_person.last_name
                sales_person = utils.get_user_full_name(first_name, last_name)

            order_items = order.orderitems.all()
            for order_item in order_items:
                data.append({
                    "id": order.id,
                    "date": str(order.date) if order.date else '-',
                    "customer__company_name": order.customer.company_name if order.customer.company_name else "-",
                    "invoice_id": order.order_id,
                    "customer__phone_number": order.customer.phone_number if order.customer.phone_number else "-",
                    "product_id": order_item.product.product_id if order_item.product.product_id else "-",
                    "product_chinese_name": order_item.product.product_chinese_name if order_item.product.product_chinese_name else "-",
                    "ramarks": order_item.remarks if order_item.remarks else "-",
                    "quantity": order_item.quantity if order_item.quantity else "-",
                    "currency": order.currency if order.currency else "-",
                    "unit_price": str(order_item.selling_price) if order_item.selling_price else "-",
                    "total_price": str(order_item.total_cost) if order_item.total_cost else "-",
                    "payment_method": order.payment_method if order.payment_method else "-",
                    "delivery_date": str(order.delivery_date) if order.delivery_date else "-",
                    "order_status": str(order.order_status).capitalize() if order.order_status else "-",
                    "sales_person": sales_person,
                    "type": order.type,
                    "old_order_order_id": order.old_order.order_id if order.old_order else "-",
                    "old_order_id": order.old_order.id if order.old_order else "-",
                })

        response = {
            # 'draw': int(request.GET.get('draw', 1)),
            'recordsTotal': orders.count(),
            # 'recordsFiltered': paginator.count,
            'data': data,
            'code': 1,
        }

        if from_date and to_date:
            daterange = from_date + " - " + to_date

        return render(request, 'home/order-approval-list.html', {"order_data": data, "daterange": daterange})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/order-approval-list.html', {"order_data": data, "daterange": daterange, "error_msg": str(e)})
    

# @login_required(login_url="/login/")
# def placeOrder(request):
#     msg = ''
#     form = orderForm()
   
#     # Retrieve data from session
#     order_details = request.session.get('productDetails', [])
#     totalquantity = request.session.get('total_quantity', 0)
#     totalproductcost = request.session.get('total_product_cost', 0)
#     customer = request.session.get('customer', None)
    
#     if customer:
#         customer = Customer.objects.filter(id=customer)
#         if not customer.exists():
#             messages.error(request, "customer not exist")
#         else:
#             customer = customer.first()

#     for order_item in order_details:
#         product_id = order_item.pop('product_id')
#         if product_id:
#             product_obj = Product.objects.filter(id=product_id).first()
#             order_item['product'] = product_obj

#     applicable_vouchers = []

#     for order in order_details:
#         # Get applicable Product Combo vouchers
#         product_combo_vouchers = Voucher.objects.filter(
#             Q(voucher_type='Product Combo') &
#             Q(start_date__lte=datetime.today()) &
#             (
#                 Q(end_date__gte=datetime.today()) | Q(
#                     end_date__isnull=True)
#             ) &
#             Q(status='Valid') &
#             (
#                 Q(quota__gt=0) | Q(quota__isnull=True)
#             ) &
#             Q(product_combo__min_quantity__lte=order['quantity']) &
#             Q(product_combo__max_quantity__gte=order['quantity']) &
#             Q(product_combo__product=order['product'])
#         )                   
            
#         applicable_vouchers.extend(product_combo_vouchers)   
#     # Get applicable Discount Vouchers and Free Gifts using Q object
#     discount_vouchers = Voucher.objects.filter(
#         Q(voucher_type='Discount Voucher'),
#         Q(start_date__lte=datetime.today()) &
#         (
#             Q(end_date__gte=datetime.today()) | Q(end_date__isnull=True)
#         ) &
#         Q(status='Valid') &
#         (
#             (Q(discount_voucher__quantity=totalquantity) & (Q(discount_voucher__quantity_trigger='Equals to') | Q(discount_voucher__quantity_trigger='Less than and equals to') | Q(discount_voucher__quantity_trigger='More than and equals to'))) |
#             (Q(discount_voucher__quantity__gt=totalquantity) & (Q(discount_voucher__quantity_trigger='More than'))| Q(discount_voucher__quantity_trigger='More than and equals to')) |
#             (Q(discount_voucher__quantity__lt=totalquantity) & (Q(discount_voucher__quantity_trigger='Less than'))| Q(discount_voucher__quantity_trigger='Less than and equals to'))
#         ) |
#         (
#             (Q(discount_voucher__price=totalproductcost) & (Q(discount_voucher__amount_trigger='Equals to') | Q(discount_voucher__amount_trigger='Less than and equals to') | Q(discount_voucher__amount_trigger='More than and equals to'))) |
#             (Q(discount_voucher__price__gt=totalproductcost) & (Q(discount_voucher__amount_trigger='More than'))| Q(discount_voucher__amount_trigger='More than and equals to')) |
#             (Q(discount_voucher__price__lt=totalproductcost) & (Q(discount_voucher__amount_trigger='Less than'))| Q(discount_voucher__amount_trigger='Less than and equals to'))
#         )
#     )

#     applicable_vouchers.extend(
#         discount_vouchers.filter(discount_voucher__only_available_to__in=[
#                                 order['product'].id for order in order_details])
#     )

#     # Get applicable Discount Vouchers and Free Gifts using Q object
#     free_gift_voucher = Voucher.objects.filter(
#         Q(voucher_type='Free Gift'),
#         Q(start_date__lte=datetime.today()) &
#         (
#             Q(end_date__gte=datetime.today()) | Q(end_date__isnull=True)
#         ) &
#         Q(status='Valid') &
#         (
#             (Q(discount_voucher__quantity=totalquantity) & (Q(discount_voucher__quantity_trigger='Equals to') | Q(discount_voucher__quantity_trigger='Less than and equals to') | Q(discount_voucher__quantity_trigger='More than and equals to'))) |
#             (Q(discount_voucher__quantity__gt=totalquantity) & (Q(discount_voucher__quantity_trigger='More than'))| Q(discount_voucher__quantity_trigger='More than and equals to')) |
#             (Q(discount_voucher__quantity__lt=totalquantity) & (Q(discount_voucher__quantity_trigger='Less than'))| Q(discount_voucher__quantity_trigger='Less than and equals to'))
#         ) |
#         (
#             (Q(discount_voucher__price=totalquantity) & (Q(discount_voucher__amount_trigger='Equals to') | Q(discount_voucher__amount_trigger='Less than and equals to') | Q(discount_voucher__amount_trigger='More than and equals to'))) |
#             (Q(discount_voucher__price__gt=totalquantity) & (Q(discount_voucher__amount_trigger='More than'))| Q(discount_voucher__amount_trigger='More than and equals to')) |
#             (Q(discount_voucher__price__lt=totalquantity) & (Q(discount_voucher__amount_trigger='Less than'))| Q(discount_voucher__amount_trigger='Less than and equals to'))
#         )
#     )
#     applicable_vouchers.extend(free_gift_voucher)


#     if request.method=="POST":
#         form = orderForm(request.POST)
#         vouchers = request.POST.get('vouchers', None)
#         vouchers = json.loads(vouchers)

#         free_gifts = request.POST.get('free_gifts', None)
#         free_gifts = json.loads(free_gifts)

#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     order_items = []
#                     for order in order_details:
#                         product = Orderitems.objects.create(**order)
#                         product.save()
#                         order_items.append(product)
                    
#                     if not form.cleaned_data['delivery_date']:
#                         delivery_date = datetime.now() + timedelta(days=7)
#                     else:
#                         delivery_date = form.cleaned_data['delivery_date']

#                     obj = Order.objects.create(
#                         delivery_date=delivery_date,
#                         delivery_cost=form.cleaned_data['delivery_cost'],
#                         total_cost=form.cleaned_data['total_cost'],
#                         payment_method=form.cleaned_data['payment_method'],
#                         other_cost=form.cleaned_data['other_cost'],
#                         customer=customer)

#                     obj.voucher.add(*vouchers)
#                     obj.free_gift.add(*free_gifts)
#                     obj.orderitems.add(*order_items)
#                     obj.save()

#                     product = Inventory.objects.filter(product_id=order["product"])
#                     product = product.first()
#                     product.total_sold_quantity = order.get('quantity')
#                     product.last_sales_date = datetime.now().date()
#                     product.save()
#                     del request.session['productDetails']
#                     del request.session['total_quantity']
#                     del request.session['total_product_cost']
#                     del request.session['customer']
#                     return redirect("order-list")
#             except Exception as e:
#                 raise e
#         else:
#             msg = form.errors

        
#     return render(request, "home/order.html", {"orderlist":order_details, 
#                                                "customer":customer,
#                                                "vouchers":applicable_vouchers, 
#                                                "total_quantity":totalquantity, 
#                                                "total_product_cost":totalproductcost, 
#                                                'form': form, 
#                                                'msg':msg})


@login_required(login_url="/login/")
def orderGet(request, id):
    form = OrderConfirmationForm()
    data_dict = {}
    order_form = orderForm()
    items_data = {}
    address_data = []
    sales_person_data = []
    try:
        # sales_persons = User.objects.filter(is_active=True, role__in=["seller", "staff"]).values("id", "username", "first_name", "last_name")
        # for sale_person in sales_persons:
        #     first_name = sale_person["first_name"]
        #     last_name = sale_person["last_name"]
        #     sales_person = utils.get_user_full_name(first_name, last_name)
            
        #     sales_person_data.append({
        #         "id": sale_person["id"],
        #         "full_name": sales_person if sales_person else "",
        #     })
            
        sales_person_data = []
        system_parameters_data = SystemParameters.objects.filter(is_deleted=False).all()
        for system_param in system_parameters_data:
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

        order = Order.objects.get(id=id)

        if not order:
            msg = "order not found"
            return render(request, 'home/orderconfirmation.html', {"form": form, "msg": msg})

        sales_person = ""
        if order.customer.sale_person:
            first_name = order.customer.sale_person.first_name
            last_name = order.customer.sale_person.last_name
            sales_person = utils.get_user_full_name(first_name, last_name)

        data_dict = {
            "id": order.id,
            "order_id": order.order_id,
            "type": order.type,
            "phone": order.customer.phone_number if order.customer.phone_number else "-",
            "delivery_address": order.delivery_address if order.delivery_address else "-",
            "order_date": datetime.strptime(str(order.date), "%Y-%m-%d").strftime("%m/%d/%Y") if order.date else "-",
            "company_name": order.customer.company_name if order.customer.company_name else "-",
            "delivery_comment": order.customer.delivery_comments if order.customer.delivery_comments else "",
            "delivery_date": datetime.strptime(str(order.delivery_date), "%Y-%m-%d").strftime("%m/%d/%Y") if order.delivery_date else "",
            "delivery_cost": order.currency + " " + str(order.delivery_cost) if order.delivery_cost else "-",
            "order_amount": order.currency + " " + str(order.total_cost) if order.total_cost else "-",
            "payment_method": order.payment_method,
            # "remarks": order.remarks,
            "other_cost": order.currency + " " + str(order.other_cost) if order.other_cost else "-",
            # "status": order.status,
            "customer_id": order.customer.customer_id if order.customer.customer_id else "-",
            "payment_status": order.payment_status if order.payment_status else "",
            "customer_name": order.customer.name if order.customer.name else "-",
            "delivery_status": order.delivery_status if order.delivery_status else "",
            "sales_person": sales_person,
            "payment_date": datetime.strptime(str(order.payment_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%m/%d/%Y %H:%M") if order.payment_date else '-',
            "delivery_method": order.delivery_method if order.delivery_method else "",
            "order_status": order.order_status if order.order_status else "",
            "manual_cost": order.currency + " " + str(order.manual_cost) if order.manual_cost else "-",
            "orderitems": [],
            "freegifts":[],
            "payment_record": os.path.basename(str(order.payment_record)) if str(order.payment_record).strip() else "",
            "can_change_sales_person": order.can_change_sales_person,
        }

        total_qty = 0
        for order_item in order.orderitems.all():
            items_data[order_item.product_id] = {"remarks": order_item.remarks if order_item.remarks else "", "quantity": order_item.quantity}
            total_qty += int(order_item.quantity)  if order_item.quantity else 0
            data_dict['orderitems'].append({
                "prod_id": order_item.product_id,
                "product_id": order_item.product.product_id,
                "product_chinese_name": order_item.product.product_chinese_name,
                "product_english_name": order_item.product.product_english_name,
                "remark": order_item.remarks if order_item.remarks else "",
                "selling_price": order.currency + " " + str(order_item.selling_price) if order_item.selling_price else "-",
                "sub_total": order.currency + " " + str(order_item.total_cost) if order_item.total_cost else "-",
                "purchase_quantity": order_item.quantity,
                "delivered_quantity": order_item.delivered_quantity,
                "damage_quantity": order_item.damage_quantity
            })

        data_dict["total_qty"] = total_qty

        if order.customer_id:
            address_data = list(Address.objects.filter(customer_id=order.customer_id).values_list("address_line", flat=True))
        # for product in order.free_gift.all():
        #     data_dict['freegifts'].append({
        #         "product_id": product.product_id,
        #         "product_chinese_name": product.product_chinese_name,
        #         "product_english_name": product.product_english_name
        #     })
        return render(request, 'home/order-deatils.html', {"form": form, "order": data_dict, "order_form": order_form, "items_data": items_data, "address_data": address_data, "role": request.user.role, "sales_person_data": sales_person_data})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/order-deatils.html', {"form": form, "order": data_dict, "order_form": order_form, "items_data": items_data, "address_data": address_data, "role": request.user.role, "sales_person_data": sales_person_data, "error_msg": str(e)})


@login_required(login_url="/login/")
def order_approval_get(request, id):
    form = OrderConfirmationForm()
    order_form = orderForm()
    data_dict = {}
    items_data = {}
    try:
        order = Order.objects.get(id=id)

        if not order:
            msg = "order not found"
            return render(request, 'home/orderconfirmation.html', {"form": form, "msg": msg})

        sales_person = "-"
        if order.customer.sale_person:
            first_name = order.customer.sale_person.first_name
            last_name = order.customer.sale_person.last_name
            sales_person = utils.get_user_full_name(first_name, last_name)

        data_dict = {
            "id": order.id,
            "order_id": order.order_id,
            "type": order.type,
            "phone": order.customer.phone_number if order.customer.phone_number else "-",
            "delivery_address": order.delivery_address if order.delivery_address else "-",
            "order_date": datetime.strptime(str(order.date), "%Y-%m-%d").strftime("%m/%d/%Y") if order.date else "-",
            "company_name": order.customer.company_name if order.customer.company_name else "-",
            "delivery_comment": order.customer.delivery_comments if order.customer.delivery_comments else "-",
            "delivery_date": datetime.strptime(str(order.delivery_date), "%Y-%m-%d").strftime("%m/%d/%Y") if order.delivery_date else "-",
            "delivery_cost": order.currency + " " + str(order.delivery_cost) if order.delivery_cost else "-",
            "order_amount": order.currency + " " + str(order.total_cost) if order.total_cost else "-",
            "payment_method": order.payment_method if order.payment_method else "-",
            # "remarks": order.remarks,
            "other_cost": order.currency + " " + str(order.other_cost) if order.other_cost else "-",
            # "status": order.status,
            "customer_id": order.customer.customer_id if order.customer.customer_id else "-",
            "payment_status": order.payment_status if order.payment_status else "-",
            "customer_name": order.customer.name if order.customer.name else "-",
            "delivery_status": order.delivery_status if order.delivery_status else "-",
            "sales_person": sales_person,
            "payment_date": datetime.strptime(str(order.payment_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%m/%d/%Y %H:%M") if order.payment_date else '-',
            "delivery_method": order.delivery_method if order.delivery_method else "-",
            "order_status": str(order.order_status).capitalize() if order.order_status else "-",
            "manual_cost": order.currency + " " + str(order.manual_cost) if order.manual_cost else "-",
            "orderitems": [],
            "freegifts":[],
            "payment_record": os.path.basename(str(order.payment_record)) if str(order.payment_record).strip() else "-",
        }

        total_qty = 0
        for order_item in order.orderitems.all():
            items_data[order_item.product_id] = {"remakrs": order_item.remarks if order_item.remarks else "", "quantity": order_item.quantity}
            total_qty += int(order_item.quantity)  if order_item.quantity else 0
            data_dict['orderitems'].append({
                "product_id": order_item.product_id,
                "product_id": order_item.product.product_id,
                "product_chinese_name": order_item.product.product_chinese_name,
                "product_english_name": order_item.product.product_english_name,
                "remark": order_item.remarks if order_item.remarks else "",
                "selling_price": order.currency + " " + str(order_item.selling_price) if order_item.selling_price else "-",
                "sub_total": order.currency + " " + str(order_item.total_cost) if order_item.total_cost else "-",
                "purchase_quantity": order_item.quantity,
                "delivered_quantity": order_item.delivered_quantity,
                "damage_quantity": order_item.damage_quantity
            })

        data_dict["total_qty"] = total_qty
        # for product in order.free_gift.all():
        #     data_dict['freegifts'].append({
        #         "product_id": product.product_id,
        #         "product_chinese_name": product.product_chinese_name,
        #         "product_english_name": product.product_english_name
        #     })
        return render(request, 'home/order-approval-deatils.html', {"form": form, "order": data_dict, "order_form": order_form, "items_data": items_data, "role": request.user.role})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/order-approval-deatils.html', {"form": form, "order": data_dict, "order_form": order_form, "items_data": items_data, "role": request.user.role, "error_msg": str(e)})


@login_required(login_url="/login/")
def pending_order_approve(request, id):
    try:
        new_order = Order.objects.filter(id=id).first()
        if new_order.old_order_id:
            old_order = Order.objects.filter(id=new_order.old_order_id).update(is_deleted=True)
        new_order.order_status = "pending payment"
        new_order.is_approve = True
        # new_order.status = "approved"
        new_order.save()

        return redirect("order-approval-list")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@login_required(login_url="/login/")
def pending_order_reject(request, id):
    try:
        new_order = Order.objects.filter(id=id).first()
        if new_order.old_order_id:
            old_order = Order.objects.filter(id=new_order.old_order_id).update(order_status="pending payment")
        new_order.order_status = "rejected"
        # new_order.status = "rejected"
        new_order.is_deleted = True
        new_order.save()

        return redirect("order-approval-list")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@login_required(login_url="/login/")
def confirmOrderDelivery(request, id):
    msg = ''
    order = Order.objects.get(id=id)
    form = OrderConfirmationForm()

    if not order:
        msg = _("order not found")
        return render(request, 'home/orderconfirmation.html', {"form": form, "msg": msg})

    form = OrderConfirmationForm(initial={
        'status': order.status,
    })

    data_dict = {
        "id": order.id,
        "delivery_date": order.delivery_date,
        "delivery_cost": order.delivery_cost,
        "total_cost": order.total_cost,
        "payment_method": order.payment_method,
        "remarks": order.remarks,
        "other_cost": order.other_cost,
        "status": order.status,
        "orderitems": [],
        "freegifts":[]
    }

    for purchase_item in order.orderitems.all():
        data_dict['orderitems'].append({
            "product_id": purchase_item.product.product_id,
            "product_chinese_name": purchase_item.product.product_chinese_name,
            "product_english_name": purchase_item.product.product_english_name,
            "selling_price": purchase_item.selling_price,
            "sub_total": purchase_item.total_cost,
            "order_quntity": purchase_item.quantity,
            "delivered_quantity": purchase_item.delivered_quantity,
            "damage_quantity": purchase_item.damage_quantity,
        })

    for product in order.free_gift.all():
        data_dict['freegifts'].append({
            "product_id": product.product_id,
            "product_chinese_name": product.product_chinese_name,
            "product_english_name": product.product_english_name
        })

    if request.method == "POST":
        form = OrderConfirmationForm(request.POST, instance=order)

        # Exclude the 'status' field from form validation
        form.save()
        del form.fields['status']

        # Retrieve delivered and damage quantities from POST data
        quantities = json.loads(request.POST.get('quantity', '{}'))

        try:
            with transaction.atomic():
                # products = order.purchase_items.filter(product__product_id=quantity['product_id'])
                for quantity in quantities:
                    orders = order.orderitems.filter(
                        product__product_id=quantity.get('product_id', ''))
                    orderitem = orders.first()

                    if quantity['delivered_quantity'] != '':
                        orderitem.delivered_quantity = quantity['delivered_quantity']
                    else:
                        orderitem.delivered_quantity = 0
                        quantity['delivered_quantity'] = 0

                    if quantity['damage_quantity'] != '':
                        orderitem.damage_quantity = quantity['damage_quantity']
                    else:
                        orderitem.damage_quantity = 0
                        quantity['damage_quantity'] = 0

                    orderitem.save()

                    product = Inventory.objects.filter(
                        product__product_id=quantity.get('product_id', ''))
                    product = product.first()
                    product.total_sold_quantity = product.total_purchased_quantity - \
                        (int(quantity['delivered_quantity']) +
                         int(quantity['damage_quantity']))
                    product.total_stock_out_quantity = int(
                        quantity['delivered_quantity'])
                    product.save()

            msg = _("order updated successfully")

            return redirect(f"order-get", id=id)
        except Exception as e:
            msg = f"Error updating order: {str(e)}"

    return render(request, 'home/orderconfirmation.html', {"form": form, "order": data_dict, "msg": msg})


@login_required(login_url="/login/")
def OrderDelete(request, id):
    msg = ""
    form = orderForm()
    data_arr = []

    try:
        Order.objects.filter(id=id).delete()
        msg = _("Order deleted successfully")
        return redirect("order-list")
    except Exception as e:
        msg = f"Unable to delete due to this error:{e}"

    # orders = Order.objects.all()

    # for order in orders:
    #     data_dict = {
    #         "id": order.id,
    #         "delivery_date": order.delivery_date,
    #         "delivery_cost": order.delivery_cost,
    #         "total_cost": order.total_cost,
    #         "payment_method": order.payment_method,
    #         "remarks": order.remarks,
    #         "status": order.status,
    #         "orderitems": []
    #     }

    #     for order_item in order.orderitems.all():
    #         data_dict['orderitems'].append({
    #             "product_id": order_item.product.product_id,
    #             "product_chinese_name": order_item.product.product_chinese_name,
    #             "product_english_name": order_item.product.product_english_name,
    #             "sub_total": order_item.total_cost,
    #             "order_quntity": order_item.quantity
    #         })

    #     data_arr.append(data_dict)

    # return render(request, 'home/order-list.html', {"form": form, "orders": data_arr, "msg": msg})
        

@method_decorator(csrf_exempt, name='dispatch')
class SearchCustomer(View):

    def post(self, request):
        if not request.body:
            raise ValueError("Empty JSON data")
        data = json.loads(request.body.decode("utf-8"))

        query = Q()
        query.add(Q(customer_id__icontains=data['keyword']) |
            Q(name__icontains=data['keyword']) |
            Q(company_name__icontains=data['keyword']) |
            Q(phone_number__icontains=data['keyword']), query.connector)
        query.add(~Q(status__in=["draft"]), query.connector)

        customers = Customer.objects.filter(query).prefetch_related('addresses')

        customer_address_li = []
        for customer in customers:
            customer_add = []
            customer_address = customer.addresses.first()
            # for cust_add in customer_address:
            if customer_address:
                customer_add.append(customer_address.address_line)
                if customer_address.address_2:
                    customer_add.append(customer_address.address_2)
                if customer_address.address_3:
                    customer_add.append(customer_address.address_3)
            sale_person = ""
            if customer.sale_person:
                sale_person = utils.get_user_full_name(customer.sale_person.first_name, customer.sale_person.last_name)

            customer_address_li.append({
                "id": customer.id,
                "customer_id": customer.customer_id,
                "name": customer.name if customer.name else "",
                "english_name": customer.english_name if customer.english_name else "",
                "company_name": customer.company_name if customer.company_name else "",
                "company_english_name": customer.company_english_name if customer.company_english_name else "",
                "phone_number": customer.phone_number if customer.phone_number else "",
                "phone_number_2": customer.phone_number_2 if customer.phone_number_2 else "",
                "customer_comments": customer.customer_comments if customer.customer_comments else "",
                "delivery_comments": customer.delivery_comments if customer.delivery_comments else "",
                "sale_person": sale_person,
                "address_line": customer_add,
            })
        # json_data = serialize('json', customers)
        # return JsonResponse(json_data, safe=False)
        return HttpResponse(json.dumps({"code": 1, "customer_address": customer_address_li}), content_type="json")
    

@login_required(login_url="/login/")
def OrderNewcreate(request):
    try:
        permission = Permissions.objects.filter(role=request.user.role, permission="can_edit_selling_price").values("permission", "is_permission").first()
        can_edit_selling_price = False
        if permission:
            can_edit_selling_price = permission["is_permission"]

        # sales_persons = User.objects.filter(is_active=True, role__in=["seller", "staff"]).values("id", "username", "first_name", "last_name")
        # sales_person_data = []
        # for sale_person in sales_persons:
        #     first_name = sale_person["first_name"]
        #     last_name = sale_person["last_name"]
        #     sales_person = utils.get_user_full_name(first_name, last_name)
            
        #     sales_person_data.append({
        #         "id": sale_person["id"],
        #         "full_name": sales_person if sales_person else "",
        #     })

        msg=''

        products = Product.objects.exclude(status="draft").values("id", "product_id", "product_chinese_name", "product_english_name", 
                                          "selling_price", "sales_currency", "unit_of_measurement",
                                          "unit_weight").order_by('-id')
        product_ids = list(products.values_list("id", flat=True))
        inventory_id_stock = {}
        inventory_data = Inventory.objects.filter(product_id__in=product_ids, current_quantity__gt=0).values("product_id", "current_quantity")
        for inventory in inventory_data:
            if inventory["product_id"] not in inventory_id_stock:
                inventory_id_stock[inventory["product_id"]] = inventory["current_quantity"]
        products_data = []
        for product in products:
            selling_price = product["selling_price"] if product["selling_price"] else "-"
            selling_price_with_currency = product["selling_price"]
            if product["sales_currency"]:
                selling_price_with_currency = product["sales_currency"] + " " + str(product["selling_price"])

                if (str(product["sales_currency"]).replace("$", "D")).lower() != "hkd":
                    hkd_price = utils.convert_currency(float(product["selling_price"]), str(product["sales_currency"]).replace("$", "D"), 'HKD')
                    if hkd_price:
                        selling_price = hkd_price
            if product["id"] in inventory_id_stock:
                products_data.append({
                    "id": product["id"],
                    "product_id": product["product_id"] if product["product_id"] else "-",
                    "product_chinese_name": product["product_chinese_name"] if product["product_chinese_name"] else "-",
                    "product_english_name": product["product_english_name"] if product["product_english_name"] else "-",
                    "currency": "HKD",
                    "selling_price": round(selling_price, 2),
                    "selling_price_with_currency": selling_price_with_currency,
                    "stock": inventory_id_stock[product["id"]] if product["id"] in inventory_id_stock and inventory_id_stock[product["id"]] else "0",
                    "specification":f"{product['unit_weight']} {product['unit_of_measurement']}" if product['unit_weight'] and product["unit_of_measurement"] else "-"
                })

        sales_person_data = []
        system_parameters_data = SystemParameters.objects.filter(is_deleted=False).all()
        for system_param in system_parameters_data:
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
        
        orderform = orderForm()
        customerform = CustomerSmallForm()
        if request.method == "POST":

            delivery_comments = request.POST.get('delivery_comments')
            total_cost = request.POST.get('total_cost')
            order_details = request.POST.get('productDetails', None)
            currency = request.POST.get('currency')
            order_details = json.loads(order_details)

            totalquantity = request.POST.get('total_quantity', None)
            totalquantity = json.loads(totalquantity)

            totalproductcost = request.POST.get('total_product_cost', None)
            totalproductcost = json.loads(totalproductcost)

            total_cost_after_discount = request.POST.get('total_cost_after_discount')
            total_cost_after_discount = json.loads(total_cost_after_discount)
            
            customer_id = request.POST.get('selected_customer', None)
            is_submit = request.POST.get("is_submit")

            if customer_id:
                customer_id = json.loads(customer_id)

            orderform = orderForm(request.POST)
            # vouchers = request.POST.get('vouchers', None)
            # vouchers = json.loads(vouchers)

            # free_gifts = request.POST.get('free_gifts', None)
            # free_gifts = json.loads(free_gifts)

            customerform = CustomerSmallForm(request.POST)
            if not customerform.is_valid():
                messages.error(request, "Customer form is not valid")

            exist_order = Order.objects.order_by("-id").first()
            
            if orderform.is_valid():
                # try:
                with transaction.atomic():
                    
                    order_items = []
                    for order in order_details:
                        product = Orderitems.objects.create(**order)
                        product.save()
                        order_items.append(product)
                        if order["selling_price"] >= 0:
                            Product.objects.filter(id=int(order["product_id"])).update(selling_price=float(order["selling_price"]), sales_currency=currency)

                    order = orderform.save(commit=False)
                    if not customer_id:
                        # last_customer = Customer.objects.order_by("-id").first()
                        customer = customerform.save()
                        customer.sale_person_id = int(request.POST.get("sales_person")) if request.POST.get("sales_person") else None
                        customer.created_by = request.user
                        order.customer_id = customer.id
                        # if last_customer and last_customer.customer_id:
                        customer.customer_id = f"C{customer.id:05}"
                        # else:
                        #     customer.customer_id = f"C{1:05}"
                        
                        customer.save()
                        Address.objects.create(address_line=orderform.cleaned_data.get('delivery_address'), customer=customer)
                    else:
                        exist_customer = Customer.objects.filter(customer_id=customer_id).first()
                        exist_customer.delivery_comments = delivery_comments
                        exist_customer.save()
                        order.customer_id = int(exist_customer.id)

                    
                    if not orderform.cleaned_data['delivery_date']:
                        orderform.delivery_date = datetime.now() + timedelta(days=7)
                    else:
                        orderform.delivery_date = orderform.cleaned_data['delivery_date']

                    # obj.voucher.add(*vouchers)
                    # obj.free_gift.add(*free_gifts)
                    order.save()

                    if str(order.payment_status).lower() == "pending":
                        order.customer.status = "converted customer"
                        order.customer.save()

                    next_num = 10
                    if exist_order:
                        last_two_num = exist_order.order_id[-2:]
                        next_num = int(last_two_num) + 1

                    order.order_id="BT" + datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").strftime("%Y%m%d") + str(next_num)
                    order.user=request.user
                    if total_cost_after_discount:
                        order.total_cost=float(total_cost_after_discount)
                    order.date=datetime.strptime(request.POST["date"], "%m/%d/%Y") if request.POST["date"] else datetime.now().strftime("%Y-%m-%d")
                    order.orderitems.add(*order_items)
                    if str(is_submit) == "false":
                        order.order_status = "draft"
                    order.save()
                    if order.approval_comments and request.user.role not in ["admin", "staff"] and str(is_submit) == "true":
                        Order_notification.objects.create(order_id=order.id, approval_for="sales_person")
                        Order_notification.objects.create(order_id=order.id, approval_for="sales_order")
                        order.order_status = "pending approval"
                    elif not order.approval_comments and request.user.role not in ["admin", "staff"] and str(is_submit) == "true":
                        Order_notification.objects.create(order_id=order.id, approval_for="sales_order")
                        order.order_status = "pending approval"
                    else:
                        order.approval_comments = None
                    
                    if order.payment_method in ["Cheque", "cheque", "COD", "cod"]:
                        today = date.today()
                        tomorrow = today + timedelta(days=1)
                        order.delivery_date = tomorrow if tomorrow else None
                    
                    order.save()
                    
                    if not order.delivery_method:
                        order.delivery_method = "SF Express"
                        order.save()
                    
                    # for item in order_details:
                    #     product = Inventory.objects.filter(product_id=item['product_id'])
                    #     product = product.first()
                    #     product.total_sold_quantity = item['quantity']
                    #     product.last_sales_date = datetime.now().date()
                    #     product.save()

                    utils.update_customer_accumulated_sales(order.customer_id)

                    return redirect("order-list")
                # except Exception as e:
                #     print("error---", e)
                #     exc_type, exc_obj, exc_tb = sys.exc_info()
                #     print("Error on line:", exc_tb.tb_lineno)
                #     raise e
            else:
                messages.error(request, "Order form is not valid")
        return render(request, "home/order.html", {"products": products_data,"orderform": orderform, "customerform":customerform, "role": request.user.role, "sales_person_data": sales_person_data, "can_edit_selling_price": can_edit_selling_price, "logged_in_user_id": request.user.id})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def order_update(request):
    try:
        if request.method == "POST":
            order_id = request.POST["order_id"]
            if order_id:
                payment_record_files = request.FILES.get("payment_record_files")
                payment_method = request.POST.get("payment_method")
                payment_status = request.POST.get("payment_status")
                delivery_method = request.POST.get("delivery_method")
                delivery_comments = request.POST.get("delivery_comments")
                order_status = request.POST.get("order_status")
                delivery_address = request.POST.get("delivery_address")
                # delivery_date = request.POST.get("delivery_date")
                order_type = request.POST.get("order_type")
                sales_person = request.POST.get("sales_person")

                order_obj = Order.objects.filter(id=int(order_id)).first()

                if request.user.role in ["admin", "staff"] or order_status == "draft":
                    items_total_price = request.POST.get("items_total_price")
                    order_items_ids = list(order_obj.orderitems.all().values_list("id", flat=True))
                    product_details = json.loads(request.POST.get("productDetails"))
                    if product_details:
                        total_quantity = 0

                        order_items = Orderitems.objects.filter(id__in=order_items_ids)
                        for order_data in product_details:
                            total_quantity += int(order_data["quantity"])
                            for order_i in order_items:
                                if order_data["product_id"] == order_i.product_id:
                                    order_i.total_cost = order_data["total_cost"]
                                    order_i.quantity = order_data["quantity"]
                                    order_i.remarks = order_data["remarks"]
                                    order_i.save()

                        order_obj.total_quantity=total_quantity
                        order_obj.total_cost=float(items_total_price)

                # order_obj.delivery_comment=delivery_comments
                customer = Customer.objects.filter(id=order_obj.customer_id).first()
                if delivery_comments:
                    customer.delivery_comments = delivery_comments
                if sales_person:
                    customer.sale_person_id = int(sales_person)
                customer.save()
                order_obj.delivery_method=delivery_method if delivery_method else "SF Express"
                order_obj.payment_status=payment_status
                order_obj.payment_method=payment_method
                order_obj.type=order_type
                if payment_record_files:
                    order_obj.payment_record=payment_record_files
                order_obj.order_status=order_status
                order_obj.delivery_address=delivery_address
                
                if str(payment_status).lower() == "paid":
                    customer.status = "paid customer"
                    customer.save()
                    if order_obj.payment_date is None:
                        order_obj.payment_date=datetime.now()
                        
                if not order_obj.delivery_date and str(payment_status).lower() == "paid" or str(payment_method).lower() in ["cheque", "cod"]:
                    today = date.today()
                    tomorrow = today + timedelta(days=1)
                    order_obj.delivery_date=tomorrow
                    
                if str(payment_status).lower() == "paid" or str(payment_method) in ["cheque", "cod"]:
                    order_obj.delivery_status = "Pending"
                order_obj.save()

                utils.update_customer_accumulated_sales(order_obj.customer_id)
                
                file_name = ""
                if str(order_obj.payment_record).strip():
                    file_name = os.path.basename(str(order_obj.payment_record))

                payment_date = ""
                if order_obj.payment_date:
                    payment_date = datetime.strptime(str(order_obj.payment_date), "%Y-%m-%d %H:%M:%S.%f").strftime("%m/%d/%Y %H:%M")
                delivery_date = ""
                if order_obj.delivery_date:
                    delivery_date = datetime.strptime(str(order_obj.delivery_date), "%Y-%m-%d").strftime("%m/%d/%Y")

                return HttpResponse(json.dumps({"code": 1, "msg": "Order is updated!", "payment_record_files": file_name, "payment_date": str(payment_date), "delivery_date": str(delivery_date), "delivery_method": order_obj.delivery_method}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Order id is not available."}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Invalid method."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def resubmit_order(request):
    try:
        if request.method == "POST":
            order_id = request.POST["order_id"]
            if order_id:
                with transaction.atomic():
                    payment_record_files = request.FILES.get("payment_record_files")
                    payment_method = request.POST.get("payment_method")
                    delivery_method = request.POST.get("delivery_method")
                    delivery_comments = request.POST.get("delivery_comments")
                    product_details = json.loads(request.POST.get("productDetails"))
                    items_total_price = request.POST.get("items_total_price")
                    order_status = request.POST.get("order_status")
                    payment_status = request.POST.get("payment_status")
                    delivery_address = request.POST.get("delivery_address")
                    delivery_date = request.POST.get("delivery_date")
                    order_type = request.POST.get("order_type")
                    sales_person = request.POST.get("sales_person")
                    
                    order_obj = Order.objects.filter(id=int(order_id)).first()
                    # order_obj.delivery_comment=delivery_comments
                    customer = Customer.objects.filter(id=order_obj.customer_id).first()
                    if delivery_comments:
                        customer.delivery_comments = delivery_comments
                    if sales_person:
                        customer.sale_person_id = int(sales_person)
                    customer.save()
                    order_obj.delivery_method=delivery_method if delivery_method else "SF Express"
                    order_obj.payment_method=payment_method
                    order_obj.payment_status=payment_status
                    order_obj.type=order_type
                    if payment_record_files:
                        order_obj.payment_record=payment_record_files
                    order_obj.order_status="pending reapproval"
                    # order_obj.status="cancelled"
                    order_obj.delivery_address=delivery_address
                    order_obj.delivery_date=datetime.strptime(str(delivery_date), "%m/%d/%Y") if delivery_date.strip() else None
                    if str(payment_status).lower() == "paid" and order_obj.payment_date is None:
                        order_obj.payment_date=datetime.now()
                        
                    if str(payment_status).lower() == "paid" or payment_method in ["Cheque", "cheque", "COD", "cod"]:
                        order_obj.delivery_status = "Pending"
                    order_obj.save()

                    file_name = os.path.basename(str(order_obj.payment_record)) if order_obj.payment_record else "",

                    if product_details:
                        exist_order = Order.objects.order_by("-id").first()
                        order_items_obj = []
                        total_quantity = 0

                        for order_data in product_details:
                            total_quantity += int(order_data["quantity"])
                            order_items_obj.append(Orderitems(**order_data))

                        if order_items_obj:
                            Orderitems.objects.bulk_create(order_items_obj)

                        create_order_obj = Order.objects.create(
                            customer_id=order_obj.customer_id,
                            delivery_cost=order_obj.delivery_cost,
                            delivery_date=order_obj.delivery_date,
                            delivery_address=order_obj.delivery_address,
                            delivery_comment=order_obj.delivery_comment,
                            delivery_method=order_obj.delivery_method,
                            total_quantity=total_quantity,
                            other_cost=order_obj.other_cost,
                            total_cost=float(items_total_price),
                            manual_cost=order_obj.manual_cost,
                            payment_method=order_obj.payment_method,
                            type=order_obj.type,
                            currency=order_obj.currency,
                            date=datetime.now().strftime("%Y-%m-%d"),
                            user_id=request.user.id if request.user else None,
                            payment_record=payment_record_files if payment_record_files else order_obj.payment_record,
                            # status="pending approval",
                            old_order_id=order_obj.id,
                            # order_status="pending approval",
                            payment_status=order_obj.payment_status,
                            payment_date=order_obj.payment_date,
                            is_approve=False,
                        )

                        if exist_order:
                            last_two_num = exist_order.order_id[-2:]
                            next_num = int(last_two_num) + 1
                        
                            create_order_obj.order_id="BT" + datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").strftime("%Y%m%d") + str(next_num)
                        create_order_obj.orderitems.add(*order_items_obj)
                        create_order_obj.save()
                        
                        return HttpResponse(json.dumps({"code": 1, "msg": "Success.", "payment_record_files": file_name}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")
    

@login_required(login_url="/login/")
def cancel_order(request, id):
    try:
        order_obj = Order.objects.filter(id=id).first()
        order_obj.order_status = "cancelled"
        order_obj.is_deleted = True
        order_obj.save()
        
        utils.update_customer_accumulated_sales(order_obj.customer_id)
        return redirect("order-list")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@login_required(login_url="/login/")
def download_payment_record(request, id):
    try:
        payment_attach = Order.objects.filter(id=id).values("payment_record").first()
        file_path = payment_attach["payment_record"]
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:   
                response = HttpResponse(file.read())
                response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(str(file_path))
                return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@login_required(login_url="/login/")
def order_list_export(request):
    try:
        query = Q()
        from_date = request.GET["from_date"] if "from_date" in request.GET else ""
        to_date = request.GET["to_date"] if "to_date" in request.GET else ""

        if from_date and to_date:
            start_date = datetime.strptime(from_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            end_date = datetime.strptime(to_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            query.add(Q(date__range=(start_date, end_date)), query.connector)

        if request.user.role == "seller":
            query.add(Q(user_id=request.user.id), query.connector)

        query.add(Q(is_deleted=False), query.connector)
        query.add(Q(is_approve=True), query.connector)
        query.add(~Q(order_status__in=["cancelled", "rejected"]), query.connector)

        orders = Order.objects.filter(query).order_by("-id")

        data = []
        for order in orders:
            sales_person = ""
            if order.customer.sale_person:
                first_name = order.customer.sale_person.first_name
                last_name = order.customer.sale_person.last_name
                sales_person = utils.get_user_full_name(first_name, last_name)

            order_items = order.orderitems.all()
            for order_item in order_items:
                data.append({
                    "Created On": datetime.strptime(str(order.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                    "Date": str(order.date) if order.date else '',
                    "Company Name": order.customer.company_name if order.customer.company_name else "",
                    "Invoice ID": order.order_id,
                    "Phone": order.customer.phone_number if order.customer.phone_number else "",
                    "Product ID": order_item.product.product_id if order_item.product.product_id else "",
                    "Product Name": order_item.product.product_chinese_name if order_item.product.product_chinese_name else "",
                    "Remark": order_item.remarks if order_item.remarks else "",
                    "Quantity": order_item.quantity if order_item.quantity else "",
                    "currency": order.currency if order.currency else "",
                    "Unit Price": str(order_item.selling_price) if order_item.selling_price else "",
                    "Total Price": str(order_item.total_cost) if order_item.total_cost else "",
                    "Payment Method": order.payment_method if order.payment_method else "",
                    "Delivery Date": str(order.delivery_date) if order.delivery_date else "",
                    "Order Status": order.order_status if order.order_status else "",
                    "Sales Person": sales_person,
                    "Type": order.type,
                })
        
        df = pd.DataFrame(data)

        now = datetime.now().strftime("%d%m%Y")
        file_path = 'media/temp/sales_order/' + str(request.user.id) + "/"
        file_name = "sales_orders_" + str(now) + ".xlsx"
        full_file_path = file_path + file_name
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        df.to_excel(full_file_path, index=False)        

        response = FileResponse(open(full_file_path, 'rb'), content_type='text/xlsx')
        response['Content-Disposition'] = f'attachment; filename=' + file_name
        return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())


@login_required(login_url="/login/")
def order_import_samplefile(request):
    try:
        full_file_path = 'sample_files/import_order_sample_file.xlsx'
        response = utils.download_samplefile(full_file_path, "import_order_sample_file.xlsx")
        return response
        # else:
        #     raise FileNotFoundError(f"File not found: {full_file_path}") 
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def order_import(request):
    try:
        if request.method == "POST":
            import_order_file = request.FILES.get("import_order_file")
            if import_order_file:
                with transaction.atomic():
                    xlsx_df = pd.read_excel(import_order_file)
                    xlsx_df = xlsx_df.map(lambda x: None if pd.isna(x) or x == '' else x)
                    order_dict = xlsx_df.to_dict(orient='records')
                    order_date = order_dict[0]["Order Date"] if "Order Date" in order_dict[0] and order_dict[0]["Order Date"] else datetime.now().strftime("%Y-%m-%d")
                    company_name = order_dict[0]["Company Name"] if "Company Name" in order_dict[0] and order_dict[0]["Company Name"] else None
                    customer_name = order_dict[0]["Customer Name"] if "Customer Name" in order_dict[0] and order_dict[0]["Customer Name"] else None
                    phone = order_dict[0]["Phone"] if "Phone" in order_dict[0] and order_dict[0]["Phone"] else None
                    product_chinese_name = order_dict[0]["Product Chinese Name"] if "Product Chinese Name" in order_dict[0] and order_dict[0]["Product Chinese Name"] else None
                    payment_method = order_dict[0]["Payment Method"] if "Payment Method" in order_dict[0] and order_dict[0]["Payment Method"] else None
                    delivery_date = order_dict[0]["Delivery Date"] if "Delivery Date" in order_dict[0] and order_dict[0]["Delivery Date"] else None
                    order_type = order_dict[0]["Type"] if "Type" in order_dict[0] and order_dict[0]["Type"] else "Invoice"
                    delivery_fee = order_dict[0]["Delivery Fee"] if "Delivery Fee" in order_dict[0] and order_dict[0]["Delivery Fee"] else 0
                    other_fee = order_dict[0]["Other Fee"] if "Other Fee" in order_dict[0] and order_dict[0]["Other Fee"] else 0
                    special_discount = order_dict[0]["Special Discount"] if "Special Discount" in order_dict[0] and order_dict[0]["Special Discount"] else 0
                    approval_comments = order_dict[0]["Approval Comments"] if "Approval Comments" in order_dict[0] and order_dict[0]["Approval Comments"] else None
                    currency = order_dict[0]["Currency"] if "Currency" in order_dict[0] and order_dict[0]["Currency"] else "HKD"
                    delivery_address = order_dict[0]["Delivery Address"] if "Delivery Address" in order_dict[0] and order_dict[0]["Delivery Address"] else None

                    customer_obj, created = Customer.objects.update_or_create(
                                    name=customer_name,
                                    defaults={
                                        "company_name": company_name,
                                        "phone_number": phone,
                                        },
                                )
                    
                    if created:
                        last_cust = Customer.objects.order_by("-id").first()
                        if last_cust and last_cust.customer_id:
                            customer_obj.customer_id = int(last_cust.customer_id) + 1
                    customer_id = customer_obj.id
                    Address.objects.update_or_create(
                            address_line=delivery_address,
                            defaults={
                                "customer_id": customer_id,
                            }
                        )

                    total_cost = 0
                    total_quantity = 0
                    order_items_obj = []
                    for order in order_dict:
                        remark = order["Remark"] if "Remark" in order and order["Remark"] else None
                        quantity = order["Quantity"] if "Quantity" in order and order["Quantity"] else 0
                        unit_price = order["Unit Price"] if "Unit Price" in order and order["Unit Price"] else 0
                        product_id = str(order["Product No"]).strip() if "Product No" in order and order["Product No"] else None
                        subtotal = float(unit_price) * int(quantity)
                        total_cost += float(subtotal)
                        total_quantity += int(quantity)
                            
                        product_data = Product.objects.filter(product_id=product_id).first()
                        if product_data:
                            order_items_obj.append(Orderitems(
                                product_id=int(product_data.id),
                                total_cost=float(subtotal),
                                selling_price=float(unit_price),
                                quantity=int(quantity),
                                remarks=remark,
                            ))
                            product_data.selling_price = float(unit_price)
                            product_data.save()

                    if order_items_obj:
                        exist_order = Order.objects.order_by("-id").first()
                        Orderitems.objects.bulk_create(order_items_obj)
                    
                        create_order_obj = Order.objects.create(
                                customer_id=customer_id,
                                delivery_cost=float(delivery_fee),
                                delivery_date=delivery_date,
                                delivery_address=delivery_address,
                                total_quantity=total_quantity,
                                other_cost=float(other_fee),
                                total_cost=float(total_cost),
                                manual_cost=float(special_discount),
                                payment_method=payment_method,
                                type=order_type,
                                currency=currency,
                                date=order_date,
                                user_id=request.user.id if request.user else None,
                                approval_comments=approval_comments,
                            )
                        
                        next_num = 10
                        if exist_order:
                            last_two_num = exist_order.order_id[-2:]
                            next_num = int(last_two_num) + 1

                        create_order_obj.order_id="BT" + datetime.strptime(str(datetime.now().date()), "%Y-%m-%d").strftime("%Y%m%d") + str(next_num)
                        create_order_obj.orderitems.add(*order_items_obj)
                        create_order_obj.save()
                        
                        utils.update_customer_accumulated_sales(create_order_obj.customer_id)
                    else:
                        return HttpResponse(json.dumps({"code": 0, "msg": "Products are not available in the system!"}), content_type="json")
                return HttpResponse(json.dumps({"code": 1, "msg": "Success."}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def get_currency_converted_price(request):
    try:
        if request.method == "POST":
            converted_price_orders = []
            converted_price_products = []
            order_list_data = json.loads(request.POST.get("order_list_data")) if request.POST.get("order_list_data") else []
            product_list_data = json.loads(request.POST.get("product_list_data")) if request.POST.get("product_list_data") else []
            to_currency = json.loads(request.POST.get("new_currency")) if request.POST.get("new_currency") else None
            show_error_cc = False
            for order in order_list_data:
                unit_price = float(order["selling_price"]) if order["selling_price"] else None
                from_currency = str(order["old_currency"]).replace("$", "D") if order["old_currency"] else None
                if unit_price and from_currency and to_currency:
                    converted_price = utils.convert_currency(unit_price, from_currency, to_currency)
                    if converted_price:
                        converted_price_orders.append({
                            "product_id" : order["product_id"],
                            "converted_price": round(converted_price, 2)
                        })
                    else:
                        show_error_cc = True
                        break
            
            for product in product_list_data:
                prod_unit_price = float(product["prod_selling_price"]) if product["prod_selling_price"] else None
                prod_from_currency = str(product["prod_old_currency"]).replace("$", "D") if product["prod_old_currency"] else None
                if prod_unit_price and prod_from_currency and to_currency:
                    prod_converted_price = utils.convert_currency(prod_unit_price, prod_from_currency, to_currency)
                    if prod_converted_price:
                        converted_price_products.append({
                            "product_id" : product["product_id"],
                            "prod_converted_price": round(prod_converted_price, 2)
                        })
                    else:
                        show_error_cc = True
                        break

            if show_error_cc:
                return HttpResponse(json.dumps({"code": 0, "msg": "Error in converting currency."}), content_type="json")
            return HttpResponse(json.dumps({"code": 1, "converted_price_orders": converted_price_orders, "converted_price_products": converted_price_products}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def get_notification(request):
    try:
        data = json.loads(request.body)
        keyword = data.get("keyword")
        order_notification_data = []
        if request.user.role in ["admin", "staff"]:
            notification_data = Order_notification.objects.filter(approval_for=keyword).values("order_id", "order__user__first_name", "order__user__last_name", "order__order_id", "created_on", "order__approval_comments").order_by("-id")
            for notify in notification_data:
                requested_user_name = utils.get_user_full_name(notify["order__user__first_name"], notify["order__user__last_name"])
                order_notification_data.append({
                    "order_id": notify["order_id"],
                    "requested_user_name": requested_user_name if requested_user_name else "-",
                    "invoice_id": notify["order__order_id"],
                    "requested_on": datetime.strptime(str(notify["created_on"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                    "approval_comments": notify["order__approval_comments"] if notify["order__approval_comments"] else "-",
                })
            notification_count = Order_notification.objects.all().count()
            
            return HttpResponse(json.dumps({"code": 1, "order_notification_data": order_notification_data, "keyword": keyword, "notification_count": notification_count}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "User doesn't have permission to perform this action."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def approve_request(request):
    try:
        if request.method == "POST":
            order_id = request.POST.get("order_id")
            keyword = request.POST.get("keyword")
            if order_id:
                order_obj = Order.objects.filter(id=order_id).first()
                if keyword == "sales_person":
                    order_obj.can_change_sales_person = True
                if keyword == "sales_order":
                    order_obj.order_status = "pending payment"
                order_obj.save()
                Order_notification.objects.filter(order_id=order_id, approval_for=keyword).delete()
                utils.update_customer_accumulated_sales(order_obj.customer_id)
                return HttpResponse(json.dumps({"code": 1, "msg": "Approved!"}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def reject_request(request):
    try:
        if request.method == "POST":
            order_id = request.POST.get("order_id")
            keyword = request.POST.get("keyword")
            if order_id:
                order_obj = Order.objects.filter(id=order_id).first()
                if keyword == "sales_person":
                    order_obj.can_change_sales_person = False
                if keyword == "sales_order":
                    order_obj.order_status = "draft"
                order_obj.save()
                Order_notification.objects.filter(order_id=order_id, approval_for=keyword).delete()

                return HttpResponse(json.dumps({"code": 1, "msg": "Rejected!"}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@login_required(login_url="/login/")
def get_notification_count(request):
    try:
        role = request.user.role
        if request.user.role in ["admin", "staff"]:
            notification_count = Order_notification.objects.all().count()
            return HttpResponse(json.dumps({"code": 1, "notification_count": notification_count, "role": role}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong.", "role": role}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def order_submit(request):
    try:
        if request.method == "POST":
            order_id = request.POST.get("order_id")
            if order_id:
                payment_record_files = request.FILES.get("payment_record_files")
                payment_method = request.POST.get("payment_method")
                payment_status = request.POST.get("payment_status")
                delivery_method = request.POST.get("delivery_method")
                delivery_comments = request.POST.get("delivery_comments")
                order_status = request.POST.get("order_status")
                delivery_address = request.POST.get("delivery_address")
                delivery_date = request.POST.get("delivery_date")
                order_type = request.POST.get("order_type")
                sales_person = request.POST.get("sales_person")

                order_obj = Order.objects.filter(id=int(order_id)).first()

                if request.user.role in ["admin", "staff"] or order_status == "draft":
                    items_total_price = request.POST.get("items_total_price")
                    order_items_ids = list(order_obj.orderitems.all().values_list("id", flat=True))
                    product_details = json.loads(request.POST.get("productDetails"))
                    if product_details:
                        total_quantity = 0

                        order_items = Orderitems.objects.filter(id__in=order_items_ids)
                        for order_data in product_details:
                            total_quantity += int(order_data["quantity"])
                            for order_i in order_items:
                                if order_data["product_id"] == order_i.product_id:
                                    order_i.total_cost = order_data["total_cost"]
                                    order_i.quantity = order_data["quantity"]
                                    order_i.remarks = order_data["remarks"]
                                    order_i.save()

                        order_obj.total_quantity=total_quantity
                        order_obj.total_cost=float(items_total_price)

                # order_obj.delivery_comment=delivery_comments
                customer = Customer.objects.filter(id=order_obj.customer_id).first()
                if delivery_comments:
                    customer.delivery_comments = delivery_comments
                if sales_person:
                    customer.sale_person_id = int(sales_person)
                customer.save()
                order_obj.delivery_method=delivery_method
                order_obj.payment_status=payment_status
                order_obj.payment_method=payment_method
                order_obj.type=order_type
                if payment_record_files:
                    order_obj.payment_record=payment_record_files
                order_obj.order_status=order_status
                order_obj.delivery_address=delivery_address
                order_obj.delivery_date=datetime.strptime(str(delivery_date), "%m/%d/%Y") if delivery_date.strip() else None
                if str(payment_status).lower() == "paid":
                    customer.status = "paid customer"
                    customer.save()
                    if order_obj.payment_date is None:
                        order_obj.payment_date=datetime.now()
                order_obj.save()

                utils.update_customer_accumulated_sales(order_obj.customer_id)
                
                order_obj = Order.objects.filter(id=order_id).first()
                if request.user.role  not in ["admin", "staff"]:
                    order_obj.order_status = "pending approval"
                    Order_notification.objects.create(order_id=order_id, approval_for="sales_order")
                else:
                    order_obj.order_status = "pending payment"
                order_obj.save()
                return HttpResponse(json.dumps({"code": 1, "msg": "success!"}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def generate_pdf(request):
    try:
        if request.method == "POST":
            order_id = request.POST.get("order_id")
            file_type = request.POST.get("file_type")
            language = request.POST.get("language")
            order_data = Order.objects.filter(id=int(order_id)).first()

            order_item_data = []
            if order_data:
                total_cost = 0
                order_items = order_data.orderitems.all()
                manual_cost = order_data.manual_cost if order_data.manual_cost else 0
                if order_data.manual_cost:
                    if (str(order_data.currency).replace("$", "D")).lower() != "hkd":
                        hkd_manual_discount_price = utils.convert_currency(float(order_data.manual_cost), str(order_data.currency).replace("$", "D"), 'HKD')
                        if hkd_manual_discount_price:
                            manual_cost = hkd_manual_discount_price
                
                for order in order_items:
                    selling_price = order.selling_price
                    if (str(order_data.currency).replace("$", "D")).lower() != "hkd":
                        hkd_price = utils.convert_currency(float(selling_price), str(order_data.currency).replace("$", "D"), 'HKD')
                        if hkd_price:
                            selling_price = hkd_price
                    subtotal = float(selling_price) * int(order.quantity)
                    total_cost += subtotal
                    order_item_data.append({
                        "code": order.product.product_id,
                        "product_name": order.product.product_chinese_name + " " + order.product.product_english_name,
                        "quantity": order.quantity,
                        "remarks": order.remarks,
                        "unit_price": round(selling_price, 2),
                        "subtotal": round(subtotal, 2),
                    })
                address = Address.objects.filter(customer_id=order_data.customer_id).values("address_line", "address_line_chinese", "address_2", "address_2_chinese", "address_3", "address_3_chinese").first()
                addresses = ""
                if address:
                    if language == "english":
                        if address["address_line"] and address["address_2"] and address["address_3"]:
                            addresses = address["address_line"] + " | " + address["address_2"] + " | " + address["address_3"]
                        elif address["address_line"] and address["address_2"] and not address["address_3"]:
                            addresses = address["address_line"] + " | " + address["address_2"]
                        elif address["address_line"] and not address["address_2"] and address["address_3"]:
                            addresses = address["address_line"] + " | " + address["address_3"]
                        elif address["address_line"] and not address["address_2"] and not address["address_3"]:
                            addresses = address["address_line"]
                    else:
                        if address["address_line_chinese"] and address["address_2_chinese"] and address["address_3_chinese"]:
                            addresses = address["address_line_chinese"] + " | " + address["address_2_chinese"] + " | " + address["address_3_chinese"]
                        elif address["address_line_chinese"] and address["address_2_chinese"] and not address["address_3_chinese"]:
                            addresses = address["address_line_chinese"] + " | " + address["address_2_chinese"]
                        elif address["address_line_chinese"] and not address["address_2_chinese"] and address["address_3_chinese"]:
                            addresses = address["address_line_chinese"] + " | " + address["address_3_chinese"]
                        elif address["address_line_chinese"] and not address["address_2_chinese"] and not address["address_3_chinese"]:
                            addresses = address["address_line_chinese"]

                contact_person = ""
                if language == "english":
                    contact_person = order_data.customer.contact_person_1
                    if order_data.customer.contact_person_1 and order_data.customer.contact_person_2:
                        contact_person = order_data.customer.contact_person_1 + " | " + order_data.customer.contact_person_2
                else:
                    contact_person = order_data.customer.contact_person_1_chinese
                    if order_data.customer.contact_person_1_chinese and order_data.customer.contact_person_2_chinese:
                        contact_person = order_data.customer.contact_person_1_chinese + " | " + order_data.customer.contact_person_2_chinese

                first_name = ""
                last_name = ""
                if order_data.customer.sale_person:
                    first_name = order_data.customer.sale_person.first_name
                    last_name = order_data.customer.sale_person.last_name
                sales_person = utils.get_user_full_name(first_name, last_name)

                mobile = ""
                if order_data.customer.phone_number:
                    mobile = order_data.customer.phone_number
                elif order_data.customer.phone_number_2:
                    mobile = order_data.customer.phone_number_2
                
                # number = 10
                # delivery_id = "DN" + str(order_data.delivery_date).replace("-", "") + str(number) if order_data.delivery_date else "DN" + str(number)
                # if order_data.delivery_id:
                #     number = int(order_data.delivery_id) + 1
                #     delivery_id = "DN" + str(order_data.delivery_date).replace("-", "") + str(number) if order_data.delivery_date else "DN" + str(number)
                    
                # order_data.delivery_id = delivery_id
                # order_data.save()

                bl_base64_with_prefix = ""
                file_path = "apps/static/assets/images/beautiland_logo.png"
                if os.path.exists(file_path):
                    with open(file_path, "rb") as file:
                        image_data = file.read()
                        base64_str = base64.b64encode(image_data).decode("utf-8")
                        bl_base64_with_prefix = "data:image/jpeg;base64," + base64_str 
                
                context = {
                    "customer_name": order_data.customer.company_english_name if language == "english" else order_data.customer.company_name,
                    "address": addresses,
                    "attention": contact_person,
                    "payment": order_data.payment_status if order_data.payment_status else "",
                    "delivery_method": order_data.delivery_method if order_data.delivery_method else "",
                    "delivery_comments": order_data.customer.delivery_comments,
                    "sales_person": sales_person,
                    "customer_id": order_data.customer.customer_id,
                    # "delivery_id": delivery_id,
                    "delivery_date": datetime.strptime(str(order_data.delivery_date), "%Y-%m-%d").strftime("%d-%b-%Y") if order_data.delivery_date else "",
                    "invoice_id": order_data.order_id,
                    "date": datetime.strptime(str(order_data.date), "%Y-%m-%d").strftime("%d-%b-%Y"),
                    "telephone": order_data.customer.landline if order_data.customer.landline else "",
                    "mobile": mobile,
                    "beautiland_logo": bl_base64_with_prefix,
                    "total_cost": round(total_cost - manual_cost, 2) if manual_cost else round(total_cost, 2),
                    "order_item_data": order_item_data,
                    "blank_space_length": range(15 - len(order_item_data)) if 15 - len(order_item_data) > 0 else range(0),
                    "language": language,
                    "manual_discount": round(manual_cost, 2) if manual_cost else 0,
                }
                
                html_string = ""
                file_name = ""
                if file_type == "delivery":
                    html_string = render_to_string('home/so_delivery_print.html', context)
                    file_name = "delivery_notes_" + order_data.order_id + "_" + str(datetime.now().date()) + ".pdf"
                if file_type == "invoice":
                    html_string = render_to_string('home/so_invoice_print.html', context)
                    file_name = "invoice_" + order_data.order_id + "_" + str(datetime.now().date()) + ".pdf"

                if html_string:
                    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
                    pdf_file = html.write_pdf()

                    response = HttpResponse(pdf_file, content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
                    return response
                
                # return render(request, 'home/so_invoice_print.html', context)
            return render(request, 'home/order-list.html', {"error_msg": "Order not found."})
        return render(request, 'home/order-list.html', {"error_msg": "Something went wrong."})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/order-list.html', {"error_msg": str(e)})


# @method_decorator(csrf_exempt, name='dispatch')
# @login_required(login_url="/login/")
# def generate_pdf(request):
#     try:
#         if request.method == "POST":
#             order_id = request.POST.get("order_id")
#             file_type = request.POST.get("file_type")
#             language = request.POST.get("language")
#             order_data = Order.objects.filter(id=int(order_id)).first()

#             order_item_data = []
#             if order_data:
#                 total_cost = 0
#                 order_items = order_data.orderitems.all()
#                 for order in order_items:
#                     selling_price = order.selling_price
#                     if (str(order_data.currency).replace("$", "D")).lower() != "hkd":
#                         hkd_price = utils.convert_currency(float(selling_price), str(order_data.currency).replace("$", "D"), 'HKD')
#                         if hkd_price:
#                             selling_price = hkd_price
#                     subtotal = float(selling_price) * int(order.quantity)
#                     total_cost += subtotal
#                     order_item_data.append({
#                         "code": order.product.product_id,
#                         "product_name": order.product.product_chinese_name,
#                         "quantity": order.quantity,
#                         "remarks": order.remarks,
#                         "unit_price": selling_price,
#                         "subtotal": subtotal,
#                     })
#                 address = Address.objects.filter(customer_id=order_data.customer_id).values("address_line", "address_2", "address_3").first()
#                 addresses = ""
#                 if address:
#                     if address["address_line"] and address["address_2"] and address["address_3"]:
#                         addresses = address["address_line"] + " | " + address["address_2"] + " | " + address["address_3"]
#                     elif address["address_line"] and address["address_2"] and not address["address_3"]:
#                         addresses = address["address_line"] + " | " + address["address_2"]
#                     elif address["address_line"] and not address["address_2"] and address["address_3"]:
#                         addresses = address["address_line"] + " | " + address["address_3"]
#                     elif address["address_line"] and not address["address_2"] and not address["address_3"]:
#                         addresses = address["address_line"]
                        
#                 contact_person = order_data.customer.contact_person_1
#                 if order_data.customer.contact_person_1 and order_data.customer.contact_person_2:
#                     contact_person = order_data.customer.contact_person_1 + " | " + order_data.customer.contact_person_2

#                 first_name = ""
#                 last_name = ""
#                 if order_data.customer.sale_person:
#                     first_name = order_data.customer.sale_person.first_name
#                     last_name = order_data.customer.sale_person.last_name
#                 sales_person = utils.get_user_full_name(first_name, last_name)

#                 mobile = ""
#                 if order_data.customer.phone_number:
#                     mobile = order_data.customer.phone_number
#                 elif order_data.customer.phone_number_2:
#                     mobile = order_data.customer.phone_number_2
                
#                 number = 10
#                 delivery_id = "DN" + str(order_data.delivery_date).replace("-", "") + str(number) if order_data.delivery_date else "DN" + str(number)
#                 if order_data.delivery_id:
#                     number = int(order_data.delivery_id) + 1
#                     delivery_id = "DN" + str(order_data.delivery_date).replace("-", "") + str(number) if order_data.delivery_date else "DN" + str(number)
                    
#                 order_data.delivery_id = number
#                 order_data.save()
                
#                 name_card_data = Customer_Files.objects.filter(customer_id=order_data.customer_id).first()
#                 base64_with_prefix = ""
#                 if name_card_data:
#                     bucket_name = settings.MEDIA_BUCKET_NAME
#                     file_name = str(name_card_data.file_name)
#                     object_name = f"{order_data.customer_id}/{file_name}"
#                     base64_with_prefix = storage_backends.get_file(bucket_name, object_name)

#                 convertable_data = {
#                     "customer_name": order_data.customer.company_name,
#                     "address": addresses,
#                     "attention": contact_person,
#                     "payment": order_data.payment_status if order_data.payment_status else "",
#                     "delivery_method": order_data.delivery_method if order_data.delivery_method else "",
#                     "delivery_comments": order_data.customer.delivery_comments,
#                     "sales_person": sales_person,
#                 }
                
#                 converted_data = {}
#                 for key, value in convertable_data.items():
#                     if language == "chinese":
#                         if utils.is_english(value):
#                             value = utils.translate_text(value, 'en', 'zh-TW')
#                         converted_data[key] = value
#                     elif language == "english":
#                         if utils.is_chinese(value):
#                             value = utils.translate_text(value, 'zh-TW', 'en')
#                         converted_data[key] = value
                            
#                 for order_item in order_item_data:
#                     for k, v in order_item.items():
#                         if k in ["product_name", "remarks"]:
#                             if language == "chinese":
#                                 if utils.is_english(v):
#                                     v = utils.translate_text(v, 'en', 'zh-TW')
#                                 order_item[k] = v
#                             elif language == "english":
#                                 if utils.is_chinese(v):
#                                     v = utils.translate_text(v, 'zh-TW', 'en')
#                                 order_item[k] = v

#                 context = {
#                     "customer_id": order_data.customer_id,
#                     "delivery_id": delivery_id,
#                     "delivery_date": datetime.strptime(str(order_data.delivery_date), "%Y-%m-%d").strftime("%d-%b-%Y") if order_data.delivery_date else "",
#                     "invoice_id": order_data.order_id,
#                     "date": datetime.strptime(str(order_data.date), "%Y-%m-%d").strftime("%d-%b-%Y"),
#                     "telephone": order_data.customer.landline if order_data.customer.landline else "",
#                     "mobile": mobile,
#                     "base_url": request.build_absolute_uri('/'),
#                     "total_cost": total_cost,
#                     "salesman_sign": base64_with_prefix,
#                     "language": language,
#                 }
                
#                 context = context | converted_data
#                 context["order_item_data"] = order_item_data

#                 html_string = ""
#                 file_name = ""
#                 if file_type == "delivery":
#                     html_string = render_to_string('home/so_delivery_print.html', context)
#                     file_name = "delivery_notes_" + order_data.order_id + "_" + str(datetime.now().date()) + ".pdf"
#                 if file_type == "invoice":
#                     html_string = render_to_string('home/so_invoice_print.html', context)
#                     file_name = "invoice_" + order_data.order_id + "_" + str(datetime.now().date()) + ".pdf"

#                 if html_string:
#                     html = HTML(string=html_string)
#                     pdf_file = html.write_pdf()

#                     response = HttpResponse(pdf_file, content_type='application/pdf')
#                     response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
#                     return response
                
#                 # return render(request, 'home/so_invoice_print.html', context)
#             return render(request, 'home/order-list.html', {"error_msg": "Order not found."})
#         return render(request, 'home/order-list.html', {"error_msg": "Something went wrong."})
#     except Exception as e:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         print("error-", e, exc_tb.tb_lineno)
#         manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
#         return render(request, 'home/order-list.html', {"error_msg": str(e)})
