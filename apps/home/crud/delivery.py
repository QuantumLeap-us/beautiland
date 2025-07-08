from django.shortcuts import redirect, render
from django.db import transaction
from django.contrib.auth.decorators import login_required
# from apps.home.tasks import process_csv_file
from apps.home.models import SystemParameters, SystemParametersForId, Inventory, Product, Supplier, Orderitems, Order
from apps.home.crud import utils, storage_backends, manager
import base64, traceback, json, os, csv
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from apps.home.model.inventory import InventoryPurchaseOrder, InventoryPurchaseOrderItems, StockInOrder, StockMove
from datetime import datetime, date
from django.db.models import Prefetch
import pandas as pd
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.db.models import Sum, Q
from django.db.models import OuterRef, Subquery
from django.template.loader import render_to_string
from apps.home.models import Address
from weasyprint import HTML
from apps.home.model.order import DeliverOrder, DeliverOrderitems
from apps.home.crud.utils import Echo


@login_required(login_url="/login/")
def delivery_list(request):
    daterange = ""
    try:
        delivery_data = []
        query = Q()
        from_date = request.GET["from_date"] if "from_date" in request.GET else ""
        to_date = request.GET["to_date"] if "to_date" in request.GET else ""
        
        wp_preset_msg_sp = SystemParameters.objects.filter(system_parameter="Whatsapp Preset Message", is_deleted=False).values("name").first()
        wp_preset_msg = wp_preset_msg_sp["name"] if wp_preset_msg_sp else ""

        if from_date and to_date:
            start_date = datetime.strptime(from_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            end_date = datetime.strptime(to_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            query.add(Q(delivery_date__range=(start_date, end_date)), query.connector)

        query.add(Q(payment_status__in=["Paid", "paid"]) | Q(payment_method__in=["COD", "cod", "Cheque", "cheque"]), query.connector)
        query.add(~Q(order_status__in=["draft", "Draft"]), query.connector)
        delivery_list = Order.objects.filter(query).values(
            "id",
            "created_date",
            "order_id",
            "order_type",
            "customer__company_name",
            "customer__phone_number",
            "delivery_address",
            "total_quantity",
            "delivery_comment",
            "payment_status",
            "payment_method",
            "payment_date",
            "delivery_date",
            "delivery_method",
            "customer__sale_person__first_name",
            "customer__sale_person__last_name",
            "customer__district_in_hk",
            "delivery_status",
        ).order_by("-created_date")
        
        order_ids = list(delivery_list.values_list("id", flat=True))
        
        delivery_order_ids = {}
        delivery_order_fees = {}
        deliver_orders = DeliverOrder.objects.filter(order_id__in=order_ids).values("delivery_id", "order_id", "delivery_fee")
        for deliver_order in deliver_orders:
            if deliver_order["order_id"] not in delivery_order_ids:
                delivery_order_ids[deliver_order["order_id"]] = [deliver_order["delivery_id"]] if deliver_order["delivery_id"] else []
                delivery_order_fees[deliver_order["order_id"]] = deliver_order["delivery_fee"]
            else:
                if deliver_order["delivery_id"] and deliver_order["delivery_id"] not in delivery_order_ids[deliver_order["order_id"]]:
                    delivery_order_ids[deliver_order["order_id"]].append(deliver_order["delivery_id"])
                    delivery_order_fees[deliver_order["order_id"]] += deliver_order["delivery_fee"]
        
        for delivery in delivery_list:
            sales_person_name = utils.get_user_full_name(delivery["customer__sale_person__first_name"], delivery["customer__sale_person__last_name"])
            
            delivery_data.append({
                "id": delivery["id"],
                "created_date": datetime.strptime(str(delivery["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "order_id": delivery["order_id"] if delivery["order_id"] else "-",
                "delivery_id": ", ".join(delivery_order_ids[delivery["id"]]) if delivery["id"] in delivery_order_ids and delivery_order_ids[delivery["id"]] else "-",
                "order_type": delivery["order_type"] if delivery["order_type"] else "-",
                "customer__company_name": delivery["customer__company_name"] if delivery["customer__company_name"] else "-",
                "customer__phone_number": delivery["customer__phone_number"] if delivery["customer__phone_number"] else "-",
                "delivery_area": delivery["customer__district_in_hk"] if delivery["customer__district_in_hk"] else "-",
                "delivery_address": delivery["delivery_address"] if delivery["delivery_address"] else "-",
                "total_quantity": delivery["total_quantity"] if delivery["total_quantity"] else "-",
                "delivery_comment": delivery["delivery_comment"] if delivery["delivery_comment"] else "-",
                "payment_status": delivery["payment_status"] if delivery["payment_status"] else "-",
                "payment_method": delivery["payment_method"] if delivery["payment_method"] else "-",
                "payment_date": datetime.strptime(str(delivery["payment_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if delivery["payment_date"] else "-",
                "delivery_status": delivery["delivery_status"] if delivery["delivery_status"] else "-",
                "delivery_date": str(delivery["delivery_date"]) if delivery["delivery_date"] else "-",
                "delivery_method": delivery["delivery_method"] if delivery["delivery_method"] else "-",
                "delivery_fee": delivery_order_fees[delivery["id"]] if delivery["id"] in delivery_order_fees else "0",
                "sales_person_name": sales_person_name if sales_person_name else "-",
            })
            
        if from_date and to_date:
            daterange = from_date + " - " + to_date

        return render(request, 'home/delivery-list.html', {"delivery_data": delivery_data, "daterange": daterange, "role": request.user.role, "wp_preset_msg": wp_preset_msg})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/delivery-list.html', {"error_msg": str(e)})


@login_required(login_url="/login/")
def delivery_list_export(request):
    try:
        delivery_data = []
        query = Q()

        query.add(Q(payment_status__in=["Paid", "paid"]) | Q(payment_method__in=["COD", "cod", "Cheque", "cheque"]), query.connector)
        query.add(~Q(order_status__in=["draft", "Draft"]), query.connector)
        delivery_list = Order.objects.filter(query).values(
            "id",
            "created_date",
            "order_id",
            "order_type",
            "customer__company_name",
            "customer__phone_number",
            "delivery_address",
            "total_quantity",
            "delivery_comment",
            "payment_status",
            "payment_method",
            "payment_date",
            "delivery_date",
            "delivery_method",
            "customer__sale_person__first_name",
            "customer__sale_person__last_name",
            "customer__district_in_hk",
            "delivery_status",
        ).order_by("-created_date")
        
        order_ids = list(delivery_list.values_list("id", flat=True))
        
        delivery_order_ids = {}
        delivery_order_fees = {}
        deliver_orders = DeliverOrder.objects.filter(order_id__in=order_ids).values("delivery_id", "order_id", "delivery_fee")
        for deliver_order in deliver_orders:
            if deliver_order["order_id"] not in delivery_order_ids:
                delivery_order_ids[deliver_order["order_id"]] = [deliver_order["delivery_id"]] if deliver_order["delivery_id"] else []
                delivery_order_fees[deliver_order["order_id"]] = deliver_order["delivery_fee"]
            else:
                if deliver_order["delivery_id"] and deliver_order["delivery_id"] not in delivery_order_ids[deliver_order["order_id"]]:
                    delivery_order_ids[deliver_order["order_id"]].append(deliver_order["delivery_id"])
                    delivery_order_fees[deliver_order["order_id"]] += deliver_order["delivery_fee"]
        
        for delivery in delivery_list:
            sales_person_name = utils.get_user_full_name(delivery["customer__sale_person__first_name"], delivery["customer__sale_person__last_name"])
            
            delivery_data.append({
                "Invoice Date": datetime.strptime(str(delivery["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "Invoice ID": delivery["order_id"] if delivery["order_id"] else "",
                "Delivery ID": ", ".join(delivery_order_ids[delivery["id"]]) if delivery["id"] in delivery_order_ids and delivery_order_ids[delivery["id"]] else "",
                "Order Type": delivery["order_type"] if delivery["order_type"] else "",
                "Company Name": delivery["customer__company_name"] if delivery["customer__company_name"] else "",
                "Phone": delivery["customer__phone_number"] if delivery["customer__phone_number"] else "",
                "Delivery Area": delivery["customer__district_in_hk"] if delivery["customer__district_in_hk"] else "",
                "Delivery Address": delivery["delivery_address"] if delivery["delivery_address"] else "",
                "Quantity": delivery["total_quantity"] if delivery["total_quantity"] else "",
                "Delivery Comment": delivery["delivery_comment"] if delivery["delivery_comment"] else "",
                "Payment Status": delivery["payment_status"] if delivery["payment_status"] else "",
                "Payment Method": delivery["payment_method"] if delivery["payment_method"] else "",
                "Payment Date": datetime.strptime(str(delivery["payment_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if delivery["payment_date"] else "",
                "Delivery Status": delivery["delivery_status"] if delivery["delivery_status"] else "",
                "Delivery Date": str(delivery["delivery_date"]) if delivery["delivery_date"] else "",
                "Delivery Method": delivery["delivery_method"] if delivery["delivery_method"] else "",
                "Delivery Fee": delivery_order_fees[delivery["id"]] if delivery["id"] in delivery_order_fees else "0",
                "Sales": sales_person_name if sales_person_name else "",
            })

        df = pd.DataFrame(delivery_data)

        now = datetime.now().strftime("%d%m%Y")
        file_path = 'media/temp/delivery/' + str(request.user.id) + "/"
        file_name = "delivery_" + str(now) + ".xlsx"
        full_file_path = file_path + file_name
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        df.to_excel(full_file_path, index=False)        

        response = FileResponse(open(full_file_path, 'rb'), content_type='text/xlsx')
        response['Content-Disposition'] = f'attachment; filename=' + file_name
        return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/delivery-list.html', {"error_msg": str(e)})
 
 
@login_required(login_url="/login/")
def delivery_list_export_breakdown(request):
    try:
        delivery_data = []
        query = Q()

        query.add(Q(payment_status__in=["Paid", "paid"]) | Q(payment_method__in=["COD", "cod", "Cheque", "cheque"]), query.connector)
        query.add(~Q(order_status__in=["draft", "Draft"]), query.connector)
        delivery_list = Order.objects.filter(query).order_by("-created_date")
        
        order_ids = list(delivery_list.values_list("id", flat=True))
        
        delivery_order_ids = {}
        delivery_order_fees = {}
        deliver_orders = DeliverOrder.objects.filter(order_id__in=order_ids).values("id", "delivery_id", 
                                                                                    "order_id",
                                                                                    "delivery_fee", 
                                                                                    "handle_by__first_name", 
                                                                                    "handle_by__last_name", 
                                                                                    "delivery_comments", 
                                                                                    "delivery_method", 
                                                                                    "warehouse_comment", 
                                                                                    "delivery_address", 
                                                                                    "delivery_date",
                                                                                    "delivered_order_status", 
                                                                                    "cancel_delivery_reason",
                                                                                    "order__created_date",
                                                                                    "order__order_id",
                                                                                    "order__order_type",
                                                                                    "order__customer__company_name",
                                                                                    "order__customer__phone_number",
                                                                                    "order__delivery_address",
                                                                                    "order__total_quantity",
                                                                                    "order__delivery_comment",
                                                                                    "order__payment_status",
                                                                                    "order__payment_method",
                                                                                    "order__payment_date",
                                                                                    "order__delivery_date",
                                                                                    "order__delivery_method",
                                                                                    "order__customer__sale_person__first_name",
                                                                                    "order__customer__sale_person__last_name",
                                                                                    "order__customer__district_in_hk",
                                                                                    "order__delivery_status").order_by("id")
        order_id_list = set(list(deliver_orders.values_list("order_id", flat=True)))
        delivery_order_items_data = []
        check_invoice_ids = []
        for deliver_order in deliver_orders:
            if deliver_order["order_id"] not in delivery_order_ids:
                delivery_order_ids[deliver_order["order_id"]] = [deliver_order["delivery_id"]] if deliver_order["delivery_id"] else []
                delivery_order_fees[deliver_order["order_id"]] = deliver_order["delivery_fee"]
            else:
                if deliver_order["delivery_id"] and deliver_order["delivery_id"] not in delivery_order_ids[deliver_order["order_id"]]:
                    delivery_order_ids[deliver_order["order_id"]].append(deliver_order["delivery_id"])
                    delivery_order_fees[deliver_order["order_id"]] += deliver_order["delivery_fee"]
                    
            delivered_order_items = DeliverOrderitems.objects.filter(deliver_order_id=deliver_order["id"]).values("id", "order_items_id", 
                                                                                                                    "deliver_order_id",
                                                                                                                    "order_items__product_id", 
                                                                                                                    "order_items__product__product_id", 
                                                                                                                    "order_items__product__product_chinese_name", 
                                                                                                                    "order_items__product__product_english_name",
                                                                                                                    "order_items__remarks", 
                                                                                                                    "delivered_quantity", 
                                                                                                                    "deliver_order__delivery_date",
                                                                                                                    "failed_delivery_quantity",
                                                                                                                    "redelivery_quantity",
                                                                                                                    "overdelivery_quantity",
                                                                                                                    "return_quantity").order_by("id")
            
            for delivered_order_item in delivered_order_items:
                sales_person_name = utils.get_user_full_name(deliver_order["order__customer__sale_person__first_name"], deliver_order["order__customer__sale_person__last_name"])
                
                delivery_order_items_data.append({
                    "id": delivered_order_item["id"],
                    "item_id": delivered_order_item["order_items_id"],
                    "prod_id": delivered_order_item["order_items__product_id"],
                    "product_id": delivered_order_item["order_items__product__product_id"],
                    "product_chinese_name": delivered_order_item["order_items__product__product_chinese_name"] or "",
                    "product_english_name": delivered_order_item["order_items__product__product_english_name"] or "",
                    "remarks": delivered_order_item["order_items__remarks"] or "",
                    "item_delivery_date": str(delivered_order_item["deliver_order__delivery_date"]) if delivered_order_item["deliver_order__delivery_date"] else "-",
                    "item_delivered_qty": delivered_order_item["delivered_quantity"],
                    "failed_delivery_qty": delivered_order_item["failed_delivery_quantity"],
                    "redelivery_qty": delivered_order_item["redelivery_quantity"],
                    "overdelivery_qty": delivered_order_item["overdelivery_quantity"],
                    "return_qty": delivered_order_item["return_quantity"],
                    
                    "deliver_order_id": deliver_order["id"],
                    "order_id": deliver_order["order_id"],
                    "delivery_id": deliver_order["delivery_id"],
                    "handle_by": utils.get_user_full_name(deliver_order["handle_by__first_name"], deliver_order["handle_by__last_name"]),
                    "delivered_delivery_comment": deliver_order["delivery_comments"] if deliver_order["delivery_comments"] else "",
                    "warehouse_comment": deliver_order["warehouse_comment"] if deliver_order["warehouse_comment"] else "",
                    "delivered_delivery_fee": deliver_order["delivery_fee"] if deliver_order["delivery_fee"] else "",
                    "delivered_delivery_date": datetime.strptime(str(deliver_order["delivery_date"]), "%Y-%m-%d").strftime("%m/%d/%Y") if deliver_order["delivery_date"] else "",
                    "delivered_delivery_method": deliver_order["delivery_method"] if deliver_order["delivery_method"] else "SF Express",
                    "delivered_delivery_address": deliver_order["delivery_address"] if deliver_order["delivery_address"] else "",
                    
                    "invoice_date": (datetime.strptime(str(deliver_order["order__created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")) if deliver_order["order_id"] not in check_invoice_ids else "",
                    "invoice_id": (deliver_order["order__order_id"] if deliver_order["order__order_id"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "order_type": (deliver_order["order__order_type"] if deliver_order["order__order_type"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "company_name": (deliver_order["order__customer__company_name"] if deliver_order["order__customer__company_name"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "phone": (deliver_order["order__customer__phone_number"] if deliver_order["order__customer__phone_number"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "delivery_area": (deliver_order["order__customer__district_in_hk"] if deliver_order["order__customer__district_in_hk"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "delivery_address": (deliver_order["order__delivery_address"] if deliver_order["order__delivery_address"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "quantity": (deliver_order["order__total_quantity"] if deliver_order["order__total_quantity"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "delivery_comment": (deliver_order["order__delivery_comment"] if deliver_order["order__delivery_comment"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "payment_status": (deliver_order["order__payment_status"] if deliver_order["order__payment_status"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "payment_method": (deliver_order["order__payment_method"] if deliver_order["order__payment_method"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "payment_date": (datetime.strptime(str(deliver_order["order__payment_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if deliver_order["order__payment_date"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "delivery_status": (deliver_order["order__delivery_status"] if deliver_order["order__delivery_status"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "delivery_date": (str(deliver_order["order__delivery_date"]) if deliver_order["order__delivery_date"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "delivery_method": (deliver_order["order__delivery_method"] if deliver_order["order__delivery_method"] else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "delivery_fee": (delivery_order_fees[deliver_order["order_id"]] if deliver_order["order_id"] in delivery_order_fees else "0") if deliver_order["order_id"] not in check_invoice_ids else "",
                    "sales": (sales_person_name if sales_person_name else "") if deliver_order["order_id"] not in check_invoice_ids else "",
                })
                check_invoice_ids.append(deliver_order["order_id"])
        
        check_order_ids = []
        for delivery in delivery_list:
            if delivery.id not in order_id_list:
                sales_person_name = utils.get_user_full_name(delivery.customer.sale_person.first_name, delivery.customer.sale_person.last_name) if delivery.customer and delivery.customer.sale_person else ""
                order_items = delivery.orderitems.all()
                for order_item in order_items:
                    delivery_data.append({
                        "id": delivery.id,
                        "invoice_date": datetime.strptime(str(delivery.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if delivery.id not in check_order_ids else "",
                        "invoice_id": (delivery.order_id if delivery.order_id else "") if delivery.id not in check_order_ids else "",
                        "order_type": (delivery.order_type if delivery.order_type else "") if delivery.id not in check_order_ids else "",
                        "company_name": (delivery.customer.company_name if delivery.customer.company_name else "") if delivery.id not in check_order_ids else "",
                        "phone": (delivery.customer.phone_number if delivery.customer.phone_number else "") if delivery.id not in check_order_ids else "",
                        "delivery_area": (delivery.customer.district_in_hk if delivery.customer.district_in_hk else "") if delivery.id not in check_order_ids else "",
                        "delivery_address": (delivery.delivery_address if delivery.delivery_address else "") if delivery.id not in check_order_ids else "",
                        "quantity": (delivery.total_quantity if delivery.total_quantity else "") if delivery.id not in check_order_ids else "",
                        "delivery_comment": (delivery.delivery_comment if delivery.delivery_comment else "") if delivery.id not in check_order_ids else "",
                        "payment_status": (delivery.payment_status if delivery.payment_status else "") if delivery.id not in check_order_ids else "",
                        "payment_method": (delivery.payment_method if delivery.payment_method else "") if delivery.id not in check_order_ids else "",
                        "payment_date": (datetime.strptime(str(delivery.payment_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if delivery.payment_date else "") if delivery.id not in check_order_ids else "",
                        "delivery_status": (delivery.delivery_status if delivery.delivery_status else "") if delivery.id not in check_order_ids else "",
                        "delivery_date": (str(delivery.delivery_date) if delivery.delivery_date else "") if delivery.id not in check_order_ids else "",
                        "delivery_method": (delivery.delivery_method if delivery.delivery_method else "") if delivery.id not in check_order_ids else "",
                        "delivery_fee": (delivery_order_fees[delivery.id] if delivery.id in delivery_order_fees else "0") if delivery.id not in check_order_ids else "",
                        "sales": (sales_person_name if sales_person_name else "") if delivery.id not in check_order_ids else "",
                        "delivery_id": "", 
                        "product_id": order_item.product.product_id,
                        "product_chinese_name": order_item.product.product_chinese_name or "-",
                        "product_english_name": order_item.product.product_english_name or "-",
                        "remarks": order_item.remarks or "-",
                        "item_delivery_date": str(order_item.delivery_date) if order_item.delivery_date else "-",
                        "item_delivered_qty": order_item.delivered_quantity,
                        "failed_delivery_qty": 0,
                        "redelivery_qty": 0,
                        "overdelivery_qty": 0,
                        "return_qty": 0,
                        "handle_by": "",
                        "delivered_delivery_comment": "",
                        "warehouse_comment": "",
                        "delivered_delivery_fee": "",
                        "delivered_delivery_date": "",
                        "delivered_delivery_method": "",
                        "delivered_delivery_address": "",
                    })
                    check_order_ids.append(delivery.id)
                    
        data_to_export = delivery_order_items_data + delivery_data

        headers = [
            "Invoice Date", "Invoice ID", "Order Type", "Company Name", "Phone",
            "Delivery Area", "Delivery Address", "Quantity", "Delivery Comment", "Payment Status",
            "Payment Method", "Payment Date", "Delivery Status", "Delivery Date", "Delivery Method", "Delivery Fee", "Sales", "Delivery ID",
            "Product ID", "Product Chinese Name", "Product English Name", "Remarks", "Product Delivery Date", "Product Delivered Quantity",
            "Failed Delivery Quantity", "Redelivery Quantity", "Overdelivery Quantity", "Return Quantity", 
            "Handle By", "Delivered Delivery Comment", "Warehouse Comment", "Delivered Delivery Fee", "Delivered Delivery Date",
            "Delivered Delivery Method", "Delivered Delivery Address",
        ]

        # Create a generator function that yields CSV rows
        def row_generator():
            yield headers  # First yield the headers

            for delivery_d in data_to_export:
                yield [
                    delivery_d["invoice_date"],
                    delivery_d["invoice_id"],
                    delivery_d["order_type"],
                    delivery_d["company_name"],
                    delivery_d["phone"],
                    delivery_d["delivery_area"],
                    delivery_d["delivery_address"],
                    delivery_d["quantity"],
                    delivery_d["delivery_comment"],
                    delivery_d["payment_status"],
                    delivery_d["payment_method"],
                    delivery_d["payment_date"],
                    delivery_d["delivery_status"],
                    delivery_d["delivery_date"],
                    delivery_d["delivery_method"],
                    delivery_d["delivery_fee"],
                    delivery_d["sales"],
                    delivery_d["delivery_id"],
                    delivery_d["product_id"],
                    delivery_d["product_chinese_name"],
                    delivery_d["product_english_name"],
                    delivery_d["remarks"],
                    delivery_d["item_delivery_date"],
                    delivery_d["item_delivered_qty"],
                    delivery_d["failed_delivery_qty"],
                    delivery_d["redelivery_qty"],
                    delivery_d["overdelivery_qty"],
                    delivery_d["return_qty"],
                    delivery_d["handle_by"],
                    delivery_d["delivered_delivery_comment"],
                    delivery_d["warehouse_comment"],
                    delivery_d["delivered_delivery_fee"],
                    delivery_d["delivered_delivery_date"],
                    delivery_d["delivered_delivery_method"],
                    delivery_d["delivered_delivery_address"],
                ]

        # Use StreamingHttpResponse for efficient memory usage
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse((writer.writerow(row) for row in row_generator()), content_type="text/csv")

        now = datetime.now().strftime("%d%m%Y")
        file_name = "delivery_breakdown_" + str(now) + ".csv"

        response['Content-Disposition'] = 'attachment; filename=' + file_name
        return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/delivery-list.html', {"error_msg": str(e)})


@login_required(login_url="/login/")
def delivery_details(request, id):
    try:
        delivery_data = {"order_items": []}
        delivered_data = []
        cancelled_delivered_data = []
        query = Q()
        query.add(Q(id=id), query.connector)
        delivery_order = Order.objects.filter(query).order_by("-created_date").first()
        delivery_status = ""
        if delivery_order:
            delivery_status = delivery_order.delivery_status
            delivery_note_sysp = SystemParameters.objects.filter(system_parameter="Delivery Note", is_deleted=False).values("name").first()
            
            order_items = delivery_order.orderitems.all()
            sales_person_name = utils.get_user_full_name(delivery_order.customer.sale_person.first_name, delivery_order.customer.sale_person.last_name) if delivery_order.customer.sale_person else "-"
            
            item_ids = list(order_items.values_list("id", flat=True))
            product_ids = list(order_items.values_list("product_id", flat=True))
            inventory = Inventory.objects.filter(product_id__in=product_ids).values("product_id", "current_quantity")
            product_stock = utils.get_dict_from_queryset(inventory, "product_id", "current_quantity")
            order_items_data = []
            for order_item in order_items:
                order_items_data.append({
                    "item_id": order_item.id,
                    "prod_id": order_item.product.id,
                    "product_id": order_item.product.product_id,
                    "product_chinese_name": order_item.product.product_chinese_name or "-",
                    "product_english_name": order_item.product.product_english_name or "-",
                    "remarks": order_item.remarks or "-",
                    "quantity": order_item.quantity,
                    "item_delivery_date": str(order_item.delivery_date) if order_item.delivery_date else "-",
                    "item_delivered_qty": order_item.delivered_quantity,
                    "stock": product_stock[order_item.product_id] if order_item.product_id in product_stock else 0,
                    "item_deliver_qty": int(order_item.quantity) - int(order_item.delivered_quantity),
                })
                
            deliver_order = DeliverOrder.objects.filter(order_id=id).only("delivery_fee").order_by("-id").first()
            
            delivery_data = {
                "id": delivery_order.id,
                "order_type": delivery_order.order_type if delivery_order.order_type else "-",
                "order_id": delivery_order.order_id if delivery_order.order_id else "-",
                "created_date": datetime.strptime(str(delivery_order.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "customer__customer_id": delivery_order.customer.customer_id if delivery_order.customer.customer_id else "-",
                "customer__company_name": delivery_order.customer.company_name if delivery_order.customer.company_name else "-",
                "customer__name": delivery_order.customer.name if delivery_order.customer.name else "-",
                "customer__phone_number": delivery_order.customer.phone_number if delivery_order.customer.phone_number else "-",
                "payment_status": delivery_order.payment_status if delivery_order.payment_status else "-",
                "payment_method": delivery_order.payment_method if delivery_order.payment_method else "-",
                "payment_date": datetime.strptime(str(delivery_order.payment_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if delivery_order.payment_date else "-",
                "sales_person_name": sales_person_name if sales_person_name else "-",
                "delivery_status": delivery_order.delivery_status if delivery_order.delivery_status else "-",
                "delivery_fee": deliver_order.delivery_fee if deliver_order and deliver_order.delivery_fee else "0",
                "delivery_comment": delivery_order.delivery_comment if delivery_order.delivery_comment else "",
                "warehouse_comment": delivery_order.warehouse_comment if delivery_order.warehouse_comment else "",
                "delivery_area": "-",
                "delivery_address": delivery_order.delivery_address if delivery_order.delivery_address else "",
                # "delivery_id": delivery_order.delivery_id if delivery_order.delivery_id else "-",
                # "total_quantity": delivery_order.total_quantity if delivery_order.total_quantity else "-",
                "delivery_date": datetime.strptime(str(delivery_order.delivery_date), "%Y-%m-%d").strftime("%m/%d/%Y") if delivery_order.delivery_date else "",
                "delivery_method": delivery_order.delivery_method if delivery_order.delivery_method else "SF Express",
                "delivery_note": delivery_note_sysp["name"] if delivery_note_sysp and delivery_note_sysp["name"] else "",
                "item_ids": item_ids,
            }
            
            delivery_data["order_items"] = order_items_data
            
            total_delivery_fee = 0
            # if delivery_status == "Partially Delivered":
            delivery_order_data = DeliverOrder.objects.filter(order_id=id, delivery_id__isnull=False).values("id", 
                                                                                                                "delivery_id", 
                                                                                                                "delivery_fee", 
                                                                                                                "handle_by__first_name", 
                                                                                                                "handle_by__last_name", 
                                                                                                                "delivery_comments", 
                                                                                                                "delivery_method", 
                                                                                                                "warehouse_comment", 
                                                                                                                "delivery_address", 
                                                                                                                "delivery_date",
                                                                                                                "delivered_order_status", 
                                                                                                                "cancel_delivery_reason").order_by("id")

            count = 0
            cancelled_count = 0
            for delivery_order in delivery_order_data:
                total_delivery_fee += delivery_order["delivery_fee"]
                
                after_sales_deliver_data = get_after_sales_deliver_data(delivery_order["id"])
                
                if delivery_order["delivered_order_status"] != "Cancelled":
                    count += 1
                    delivered_order_items = DeliverOrderitems.objects.filter(deliver_order_id=delivery_order["id"]).values("id", "order_items_id", 
                                                                                                                            "deliver_order_id",
                                                                                                                            "order_items__product_id", 
                                                                                                                            "order_items__product__product_id", 
                                                                                                                            "order_items__product__product_chinese_name", 
                                                                                                                            "order_items__product__product_english_name",
                                                                                                                            "order_items__remarks", 
                                                                                                                            "delivered_quantity", 
                                                                                                                            "deliver_order__delivery_date").order_by("id")
                    delivery_order_items_data = []
                    for delivered_order_item in delivered_order_items:
                        delivery_order_items_data.append({
                                "id": delivered_order_item["id"],
                                "item_id": delivered_order_item["order_items_id"],
                                "prod_id": delivered_order_item["order_items__product_id"],
                                "product_id": delivered_order_item["order_items__product__product_id"],
                                "product_chinese_name": delivered_order_item["order_items__product__product_chinese_name"] or "-",
                                "product_english_name": delivered_order_item["order_items__product__product_english_name"] or "-",
                                "remarks": delivered_order_item["order_items__remarks"] or "-",
                                "item_delivery_date": str(delivered_order_item["deliver_order__delivery_date"]) if delivered_order_item["deliver_order__delivery_date"] else "-",
                                "item_delivered_qty": delivered_order_item["delivered_quantity"],
                            })

                    if delivery_order_items_data:
                        delivered_data.append({
                            "id": delivery_order["id"],
                            "delivery_id": delivery_order["delivery_id"],
                            "handle_by": utils.get_user_full_name(delivery_order["handle_by__first_name"], delivery_order["handle_by__last_name"]),
                            "delivery_comment": delivery_order["delivery_comments"] if delivery_order["delivery_comments"] else "",
                            "warehouse_comment": delivery_order["warehouse_comment"] if delivery_order["warehouse_comment"] else "",
                            "delivery_fee": delivery_order["delivery_fee"] if delivery_order["delivery_fee"] else "",
                            "delivery_date": datetime.strptime(str(delivery_order["delivery_date"]), "%Y-%m-%d").strftime("%m/%d/%Y") if delivery_order["delivery_date"] else "",
                            "delivery_method": delivery_order["delivery_method"] if delivery_order["delivery_method"] else "SF Express",
                            "delivery_address": delivery_order["delivery_address"] if delivery_order["delivery_address"] else "",
                            "delivered_order_items": delivery_order_items_data,
                            "count": count,
                            "type": "",
                        })
                    if after_sales_deliver_data:
                        delivered_data.append(after_sales_deliver_data)
                else:
                    cancelled_count += 1
                    cancelled_delivered_order_items = DeliverOrderitems.objects.filter(deliver_order_id=delivery_order["id"]).values("id", "order_items_id", 
                                                                                                                            "deliver_order_id",
                                                                                                                            "order_items__product_id", 
                                                                                                                            "order_items__product__product_id", 
                                                                                                                            "order_items__product__product_chinese_name", 
                                                                                                                            "order_items__product__product_english_name",
                                                                                                                            "order_items__remarks", 
                                                                                                                            "delivered_quantity", 
                                                                                                                            "deliver_order__delivery_date")
                    cancelled_delivery_order_items_data = []
                    for cancelled_delivered_order_item in cancelled_delivered_order_items:
                        cancelled_delivery_order_items_data.append({
                                "id": cancelled_delivered_order_item["id"],
                                "item_id": cancelled_delivered_order_item["order_items_id"],
                                "prod_id": cancelled_delivered_order_item["order_items__product_id"],
                                "product_id": cancelled_delivered_order_item["order_items__product__product_id"],
                                "product_chinese_name": cancelled_delivered_order_item["order_items__product__product_chinese_name"] or "-",
                                "product_english_name": cancelled_delivered_order_item["order_items__product__product_english_name"] or "-",
                                "remarks": cancelled_delivered_order_item["order_items__remarks"] or "-",
                                "item_delivery_date": str(cancelled_delivered_order_item["deliver_order__delivery_date"]) if cancelled_delivered_order_item["deliver_order__delivery_date"] else "-",
                                "item_delivered_qty": cancelled_delivered_order_item["delivered_quantity"],
                            })

                    if cancelled_delivery_order_items_data:
                        cancelled_delivered_data.append({
                            "id": delivery_order["id"],
                            "delivery_id": delivery_order["delivery_id"],
                            "handle_by": utils.get_user_full_name(delivery_order["handle_by__first_name"], delivery_order["handle_by__last_name"]),
                            "delivery_comment": delivery_order["delivery_comments"] if delivery_order["delivery_comments"] else "",
                            "warehouse_comment": delivery_order["warehouse_comment"] if delivery_order["warehouse_comment"] else "",
                            "delivery_fee": delivery_order["delivery_fee"] if delivery_order["delivery_fee"] else "",
                            "delivery_date": datetime.strptime(str(delivery_order["delivery_date"]), "%Y-%m-%d").strftime("%m/%d/%Y") if delivery_order["delivery_date"] else "",
                            "delivery_method": delivery_order["delivery_method"] if delivery_order["delivery_method"] else "SF Express",
                            "delivery_address": delivery_order["delivery_address"] if delivery_order["delivery_address"] else "",
                            "cancelled_delivered_order_items": cancelled_delivery_order_items_data,
                            "cancelled_count": cancelled_count,
                            "delivered_order_status": delivery_order["delivered_order_status"] if delivery_order["delivered_order_status"] else "",
                            "cancel_delivery_reason": delivery_order["cancel_delivery_reason"] if delivery_order["cancel_delivery_reason"] else "",
                            "type": "",
                        })
                    if after_sales_deliver_data:
                        cancelled_delivered_data.append(after_sales_deliver_data)
                           
            response = {"delivery_data": delivery_data, 
                        "delivered_data": delivered_data, 
                        "cancelled_delivered_data": cancelled_delivered_data, 
                        "delivery_status": delivery_status, 
                        "total_delivery_fee": total_delivery_fee, 
                        "role": request.user.role}

        return render(request, 'home/delivery_details.html', response)
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/delivery_details.html', {"error_msg": str(e), "role": request.user.role})


def get_after_sales_deliver_data(deliver_order_id):
    after_sales_delivered_data = {}
    after_sales_deliver_order = DeliverOrder.objects.filter(self_deliver_order=deliver_order_id, delivery_id__isnull=False).values("id",
                                                                                                                                   "delivery_id", 
                                                                                                                                    "delivery_fee", 
                                                                                                                                    "handle_by__first_name", 
                                                                                                                                    "handle_by__last_name", 
                                                                                                                                    "delivery_comments", 
                                                                                                                                    "delivery_method", 
                                                                                                                                    "warehouse_comment", 
                                                                                                                                    "delivery_address", 
                                                                                                                                    "delivery_date",
                                                                                                                                    "delivered_order_status", 
                                                                                                                                    "cancel_delivery_reason").order_by("id").first()
    if after_sales_deliver_order:
        after_sales_delivered_order_items = DeliverOrderitems.objects.filter(deliver_order_id=after_sales_deliver_order["id"]).values("id", "order_items_id", 
                                                                                                                                    "deliver_order_id",
                                                                                                                                    "order_items__product_id", 
                                                                                                                                    "order_items__product__product_id", 
                                                                                                                                    "order_items__product__product_chinese_name", 
                                                                                                                                    "order_items__product__product_english_name",
                                                                                                                                    "order_items__remarks", 
                                                                                                                                    "delivered_quantity", 
                                                                                                                                    "deliver_order__delivery_date",
                                                                                                                                    "failed_delivery_quantity",
                                                                                                                                    "redelivery_quantity",
                                                                                                                                    "overdelivery_quantity",
                                                                                                                                    "return_quantity").order_by("id")
        
        after_sales_delivery_order_items_data = []
        for after_sales_delivered_order_item in after_sales_delivered_order_items:
            after_sales_delivery_order_items_data.append({
                    "id": after_sales_delivered_order_item["id"],
                    "item_id": after_sales_delivered_order_item["order_items_id"],
                    "prod_id": after_sales_delivered_order_item["order_items__product_id"],
                    "product_id": after_sales_delivered_order_item["order_items__product__product_id"],
                    "product_chinese_name": after_sales_delivered_order_item["order_items__product__product_chinese_name"] or "-",
                    "product_english_name": after_sales_delivered_order_item["order_items__product__product_english_name"] or "-",
                    "remarks": after_sales_delivered_order_item["order_items__remarks"] or "-",
                    "item_delivery_date": str(after_sales_delivered_order_item["deliver_order__delivery_date"]) if after_sales_delivered_order_item["deliver_order__delivery_date"] else "-",
                    "item_delivered_qty": after_sales_delivered_order_item["delivered_quantity"],
                    "failed_delivery_quantity": after_sales_delivered_order_item["failed_delivery_quantity"] or "-",
                    "redelivery_quantity": after_sales_delivered_order_item["redelivery_quantity"] or "-",
                    "overdelivery_quantity": after_sales_delivered_order_item["overdelivery_quantity"] or "-",
                    "return_quantity": after_sales_delivered_order_item["return_quantity"] or "-",
                })
        
        if after_sales_delivery_order_items_data:
            after_sales_delivered_data = {
                                "id": after_sales_deliver_order["id"],
                                "delivery_id": after_sales_deliver_order["delivery_id"],
                                "handle_by": utils.get_user_full_name(after_sales_deliver_order["handle_by__first_name"], after_sales_deliver_order["handle_by__last_name"]),
                                "delivery_comment": after_sales_deliver_order["delivery_comments"] if after_sales_deliver_order["delivery_comments"] else "",
                                "warehouse_comment": after_sales_deliver_order["warehouse_comment"] if after_sales_deliver_order["warehouse_comment"] else "",
                                "delivery_fee": after_sales_deliver_order["delivery_fee"] if after_sales_deliver_order["delivery_fee"] else "",
                                "delivery_date": datetime.strptime(str(after_sales_deliver_order["delivery_date"]), "%Y-%m-%d").strftime("%m/%d/%Y") if after_sales_deliver_order["delivery_date"] else "",
                                "delivery_method": after_sales_deliver_order["delivery_method"] if after_sales_deliver_order["delivery_method"] else "SF Express",
                                "delivery_address": after_sales_deliver_order["delivery_address"] if after_sales_deliver_order["delivery_address"] else "",
                                "delivered_order_items": after_sales_delivery_order_items_data,
                                "type": "after sales",
                            }
    return after_sales_delivered_data
    

@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def save_item_delivery(request):
    try:
        with transaction.atomic():
            if request.method == "POST":
                product_details = json.loads(request.POST.get("productDetails"))
                delivery_comment = request.POST.get("delivery_comment")
                delivery_address = request.POST.get("delivery_address")
                warehouse_comment = request.POST.get("warehouse_comment")
                delivery_date = datetime.strptime(str(request.POST.get("delivery_date")), "%m/%d/%Y").strftime("%Y-%m-%d") if request.POST.get("delivery_date") else None
                delivery_fee = request.POST.get("delivery_fee")
                order_id = request.POST.get("order_id")
                delivery_status = request.POST.get("delivery_status")

                order = Order.objects.filter(id=order_id).only("delivery_comment", "delivery_address", "delivery_date", "warehouse_comment", "delivery_status", "delivery_method").first()
                if order:
                    order.delivery_comment=delivery_comment
                    order.delivery_address=delivery_address
                    order.delivery_date=delivery_date
                    order.warehouse_comment=warehouse_comment
                    order.delivery_status=delivery_status
                    order.save()
                    
                deliver_order = DeliverOrder.objects.filter(order_id=order_id, delivery_id__isnull=True, self_deliver_order__isnull=True).only("delivery_fee", "handle_by", "delivery_comments", "delivery_method", "warehouse_comment", "delivery_address").first()
                if not deliver_order:
                    if product_details:
                        deliver_order = DeliverOrder.objects.create(order_id=order_id, 
                                                                    delivery_fee=delivery_fee, 
                                                                    handle_by=request.user,
                                                                    delivery_comments=delivery_comment, 
                                                                    delivery_method=order.delivery_method if order and order.delivery_method else "SF Express", 
                                                                    warehouse_comment=warehouse_comment, 
                                                                    delivery_address=delivery_address, 
                                                                    )
                else:
                    deliver_order.delivery_fee = delivery_fee
                    deliver_order.handle_by=request.user
                    deliver_order.delivery_comments=delivery_comment
                    deliver_order.delivery_method=order.delivery_method if order and order.delivery_method else "SF Express" 
                    deliver_order.warehouse_comment=warehouse_comment
                    deliver_order.delivery_address=delivery_address
                    deliver_order.save()
                
                deliver_order_items_obj = []
                for product_detail in product_details:
                    item_id = product_detail["item_id"]
                    deliver_qty = product_detail["deliver_qty"]
                    order_item = Orderitems.objects.filter(id=item_id).only("delivered_quantity", "delivery_date").first()
                    deliver_order_items_obj.append(DeliverOrderitems(deliver_order_id=deliver_order.id, order_items_id=item_id, delivered_quantity=deliver_qty))
                    
                    if order_item:
                        order_item.delivered_quantity += deliver_qty
                        order_item.delivery_date = date.today()
                        order_item.save()
                    
                    product_inv = Inventory.objects.filter(product_id=product_detail["product_id"]).only("current_quantity").first()
                    if product_inv:
                        product_inv.current_quantity -= deliver_qty
                        product_inv.save()
                       
                if deliver_order_items_obj:
                    DeliverOrderitems.objects.bulk_create(deliver_order_items_obj)
                                 
                return HttpResponse(json.dumps({"code": 1, "msg": "Product delivered."}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Method not allowed."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")
    

# def change_order_status(order_id):
#     order = Order.objects.filter(id=order_id).first()
#     if order:
#         order_items = order.orderitems.all()
#         status = ""
#         for order_item in order_items:
#             if order_item.delivered_quantity > 0:
#                 remain_qty = order_item.quantity - order_item.delivered_quantity
#                 if remain_qty == 0:
#                     status = "Delivered"
#                 if remain_qty > 0:
#                     status = "Partially Delivered"


@login_required(login_url="/login/")
def generate_pdf_for_delivery_note(request, order_id, deliver_id):
    try:
        file_type = "delivery"
        language = "english"
        order_data = Order.objects.filter(id=int(order_id)).first()

        order_item_data = []
        if order_data:
            total_cost = 0
            
            query = Q()
            if deliver_id:
                query.add(Q(id=int(deliver_id)), query.connector)
            else:
                query.add(Q(order_id=int(order_id)) & Q(delivery_id__isnull=True) & Q(self_deliver_order__isnull=True), query.connector)
                
            delivery_order = DeliverOrder.objects.filter(query).first()
            
            if not delivery_order:
                return HttpResponse(json.dumps({"code": 0, "msg": "There's no data for generating delivery note."}), content_type="json")
            
            # deliver_order_ids = list(DeliverOrder.objects.filter(order_id=int(order_id), delivery_id__isnull=True).values_list("id", flat=True))
            deliver_order_items = DeliverOrderitems.objects.filter(deliver_order_id=delivery_order.id)
            # order_items = order_data.orderitems.all() 
            manual_cost = order_data.manual_cost if order_data.manual_cost else 0
            if order_data.manual_cost:
                if (str(order_data.currency).replace("$", "D")).lower() != "hkd":
                    hkd_manual_discount_price = utils.convert_currency(float(order_data.manual_cost), str(order_data.currency).replace("$", "D"), 'HKD')
                    if hkd_manual_discount_price:
                        manual_cost = hkd_manual_discount_price
            
            order_items = {}
            for order in deliver_order_items:
                if order.order_items_id not in order_items:
                    order_items[order.order_items_id] = order.delivered_quantity
                else:
                    order_items[order.order_items_id] += order.delivered_quantity
            
            check_existed_products = []      
            for order in deliver_order_items:
                if order.order_items.product.product_id not in check_existed_products:
                    selling_price = order.order_items.selling_price
                    if (str(order_data.currency).replace("$", "D")).lower() != "hkd":
                        hkd_price = utils.convert_currency(float(selling_price), str(order_data.currency).replace("$", "D"), 'HKD')
                        if hkd_price:
                            selling_price = hkd_price
                    subtotal = float(selling_price) * int(order.order_items.quantity)
                    total_cost += subtotal
                    order_item_data.append({
                        "code": order.order_items.product.product_id,
                        "product_name": order.order_items.product.product_chinese_name + " " + order.order_items.product.product_english_name,
                        "quantity": order.order_items.quantity,
                        "delivered_quantity": order_items[order.order_items_id] if order.order_items_id in order_items else "",
                        "remarks": order.order_items.remarks,
                        "unit_price": round(selling_price, 2),
                        "subtotal": round(subtotal, 2),
                    })
                    check_existed_products.append(order.order_items.product.product_id)
            # address = Address.objects.filter(customer_id=order_data.customer_id).values("address_line", "address_line_chinese", "address_2", "address_2_chinese", "address_3", "address_3_chinese").first()
            # addresses = ""
            # if address:
            #     if language == "english":
            #         if address["address_line"] and address["address_2"] and address["address_3"]:
            #             addresses = address["address_line"] + " | " + address["address_2"] + " | " + address["address_3"]
            #         elif address["address_line"] and address["address_2"] and not address["address_3"]:
            #             addresses = address["address_line"] + " | " + address["address_2"]
            #         elif address["address_line"] and not address["address_2"] and address["address_3"]:
            #             addresses = address["address_line"] + " | " + address["address_3"]
            #         elif address["address_line"] and not address["address_2"] and not address["address_3"]:
            #             addresses = address["address_line"]
            #     else:
            #         if address["address_line_chinese"] and address["address_2_chinese"] and address["address_3_chinese"]:
            #             addresses = address["address_line_chinese"] + " | " + address["address_2_chinese"] + " | " + address["address_3_chinese"]
            #         elif address["address_line_chinese"] and address["address_2_chinese"] and not address["address_3_chinese"]:
            #             addresses = address["address_line_chinese"] + " | " + address["address_2_chinese"]
            #         elif address["address_line_chinese"] and not address["address_2_chinese"] and address["address_3_chinese"]:
            #             addresses = address["address_line_chinese"] + " | " + address["address_3_chinese"]
            #         elif address["address_line_chinese"] and not address["address_2_chinese"] and not address["address_3_chinese"]:
            #             addresses = address["address_line_chinese"]

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
            
            delivery_id = delivery_order.delivery_id
            if not delivery_id:
                deliver_order = DeliverOrder.objects.filter(delivery_id__isnull=False).order_by("-id").first()
                number = 10
                delivery_id = "DN" + str(order_data.delivery_date).replace("-", "") + str(number) if order_data.delivery_date else "DN" + str(number)
                if deliver_order and deliver_order.delivery_id:
                    number = int((deliver_order.delivery_id)[10:]) + 1
                    delivery_id = "DN" + str(order_data.delivery_date).replace("-", "") + str(number) if order_data.delivery_date else "DN" + str(number)
            
                new_delivery_id = DeliverOrder.objects.filter(order_id=int(order_id), delivery_id__isnull=True).update(delivery_id=delivery_id, delivery_date=date.today())
            order_data.save()

            bl_base64_with_prefix = ""
            file_path = "apps/static/assets/images/beautiland_logo.png"
            if os.path.exists(file_path):
                with open(file_path, "rb") as file:
                    image_data = file.read()
                    base64_str = base64.b64encode(image_data).decode("utf-8")
                    bl_base64_with_prefix = "data:image/jpeg;base64," + base64_str 
            
            context = {
                "customer_name": order_data.customer.company_english_name if language == "english" else order_data.customer.company_name,
                "address": delivery_order.delivery_address,
                "attention": contact_person,
                "payment": order_data.payment_status if order_data.payment_status else "",
                "delivery_method": order_data.delivery_method if order_data.delivery_method else "",
                "delivery_comments": order_data.customer.delivery_comments,
                "sales_person": sales_person,
                "customer_id": order_data.customer.customer_id,
                "delivery_id": delivery_id,
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
                file_name = "delivery_notes_" + order_data.order_id + "_" + delivery_id + "_" + str(datetime.now().date()) + ".pdf"

            if html_string:
                html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
                pdf_file = html.write_pdf()

                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
                return response
            
            # return render(request, 'home/so_invoice_print.html', context)
        # return render(request, 'home/order-list.html', {"error_msg": "Order not found."})
        return HttpResponse(json.dumps({"code": 0, "msg": "Order not found."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")
        # return render(request, 'home/order-list.html', {"error_msg": str(e)})
    

@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def cancel_delivered_order(request):
    try:
        with transaction.atomic():
            if request.method == "POST":
                cancel_deliver_id = request.POST.get("cancel_deliver_id")
                cancel_delivery_reason = request.POST.get("cancel_delivery_reason")
                if cancel_deliver_id:
                    DeliverOrder.objects.filter(id=cancel_deliver_id).update(delivered_order_status="Cancelled", cancel_delivery_reason=cancel_delivery_reason)
                    delivered_order_items = DeliverOrderitems.objects.filter(deliver_order_id=cancel_deliver_id).only("delivered_quantity", "order_items").select_related("order_items__product")
                    items_to_update = []
                    for delivered_order_item in delivered_order_items:
                        delivered_order_item.order_items.delivered_quantity -= delivered_order_item.delivered_quantity
                        items_to_update.append(delivered_order_item.order_items)  # Add the modified item to the list
                        
                        inventory = Inventory.objects.filter(product_id=delivered_order_item.order_items.product_id).only("current_quantity").first()
                        if inventory:
                            inventory.current_quantity += delivered_order_item.delivered_quantity
                            inventory.save()

                    Orderitems.objects.bulk_update(items_to_update, ['delivered_quantity'])
                    
                    return HttpResponse(json.dumps({"code": 1, "msg": "Delivered order cancelled successfully."}), content_type="json")
                return HttpResponse(json.dumps({"code": 0, "msg": "Delivered order not found."}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")
    

@login_required(login_url="/login/")
def after_sales_delivery(request, id):
    try:
        if id:
            delivery_note_sysp = SystemParameters.objects.filter(system_parameter="Delivery Note", is_deleted=False).values("name").first()

            delivered_data = {}
            delivery_order_data = DeliverOrder.objects.filter(id=id).values("id", 
                                                                            "delivery_id", 
                                                                            "delivery_fee", 
                                                                            "handle_by__first_name", 
                                                                            "handle_by__last_name", 
                                                                            "delivery_comments", 
                                                                            "delivery_method", 
                                                                            "warehouse_comment", 
                                                                            "delivery_address", 
                                                                            "delivery_date",
                                                                            "delivered_order_status", 
                                                                            "cancel_delivery_reason",
                                                                            "order__order_id",
                                                                            "order_id").first()

            if delivery_order_data:
                after_sales_deliverorder_ids = list(DeliverOrder.objects.filter(self_deliver_order_id=delivery_order_data["id"]).values_list("id", flat=True))
                after_sales_deliver_order_items = DeliverOrderitems.objects.filter(deliver_order_id__in=after_sales_deliverorder_ids).values("order_items_id", 
                                                                                                                                            "failed_delivery_quantity",
                                                                                                                                            "redelivery_quantity",
                                                                                                                                            "overdelivery_quantity",
                                                                                                                                            "return_quantity",
                                                                                                                                            "self_deliver_order_item_id").order_by("-id")
                
                after_sales_item_qty = {}
                for after_sales_item in after_sales_deliver_order_items:
                    if after_sales_item["order_items_id"] not in after_sales_item_qty:
                        after_sales_item_qty[after_sales_item["order_items_id"]] = {"failed_delivery_quantity": after_sales_item["failed_delivery_quantity"], 
                                                                                    "redelivery_quantity": after_sales_item["redelivery_quantity"], 
                                                                                    "overdelivery_quantity": after_sales_item["overdelivery_quantity"], 
                                                                                    "return_quantity": after_sales_item["return_quantity"]}
                    else:
                        after_sales_item_qty[after_sales_item["order_items_id"]]["failed_delivery_quantity"] += after_sales_item["failed_delivery_quantity"]
                        after_sales_item_qty[after_sales_item["order_items_id"]]["redelivery_quantity"] += after_sales_item["redelivery_quantity"]
                        after_sales_item_qty[after_sales_item["order_items_id"]]["overdelivery_quantity"] += after_sales_item["overdelivery_quantity"]
                        after_sales_item_qty[after_sales_item["order_items_id"]]["return_quantity"] += after_sales_item["return_quantity"]
                    
                
                delivered_order_items = DeliverOrderitems.objects.filter(deliver_order_id=delivery_order_data["id"]).values("id", 
                                                                                                                       "order_items_id", 
                                                                                                                        "deliver_order_id",
                                                                                                                        "order_items__product_id", 
                                                                                                                        "order_items__product__product_id", 
                                                                                                                        "order_items__product__product_chinese_name", 
                                                                                                                        "order_items__product__product_english_name",
                                                                                                                        "order_items__remarks", 
                                                                                                                        "delivered_quantity", 
                                                                                                                        "deliver_order__delivery_date",
                                                                                                                        "failed_delivery_quantity",
                                                                                                                        "redelivery_quantity",
                                                                                                                        "overdelivery_quantity",
                                                                                                                        "return_quantity").order_by("-id")
                delivery_order_items_data = []
                for delivered_order_item in delivered_order_items:
                    delivered_quantity = delivered_order_item["delivered_quantity"] or 0
                    item_delivered_qty = delivered_quantity
                    for after_sales_item in after_sales_deliver_order_items:
                        if delivered_order_item["id"] == after_sales_item["self_deliver_order_item_id"]:
                            failed_delivery_quantity = after_sales_item["failed_delivery_quantity"] if after_sales_item["failed_delivery_quantity"] else 0
                            redelivery_quantity = after_sales_item["redelivery_quantity"] if after_sales_item["redelivery_quantity"] else 0
                            overdelivery_quantity = after_sales_item["overdelivery_quantity"] if after_sales_item["overdelivery_quantity"] else 0
                            return_quantity = after_sales_item["return_quantity"] if after_sales_item["return_quantity"] else 0
                            
                            item_delivered_qty = delivered_quantity - (failed_delivery_quantity + redelivery_quantity + overdelivery_quantity + return_quantity)
                            
                    delivery_order_items_data.append({
                            "id": delivered_order_item["id"],
                            "item_id": delivered_order_item["order_items_id"],
                            "prod_id": delivered_order_item["order_items__product_id"],
                            "product_id": delivered_order_item["order_items__product__product_id"],
                            "product_chinese_name": delivered_order_item["order_items__product__product_chinese_name"] or "-",
                            "product_english_name": delivered_order_item["order_items__product__product_english_name"] or "-",
                            "remarks": delivered_order_item["order_items__remarks"] or "-",
                            "item_delivery_date": str(delivered_order_item["deliver_order__delivery_date"]) if delivered_order_item["deliver_order__delivery_date"] else "-",
                            "item_delivered_qty": item_delivered_qty if item_delivered_qty else 0,
                        })

                delivered_data = {
                    "id": delivery_order_data["id"],
                    "order_id": delivery_order_data["order_id"],
                    "delivery_id": delivery_order_data["delivery_id"],
                    "invoice_id": delivery_order_data["order__order_id"],
                    "warehouse_comment": delivery_order_data["warehouse_comment"] if delivery_order_data["warehouse_comment"] else "",
                    "delivery_fee": delivery_order_data["delivery_fee"] if delivery_order_data["delivery_fee"] else 0,
                    "delivery_date": datetime.strptime(str(delivery_order_data["delivery_date"]), "%Y-%m-%d").strftime("%m/%d/%Y") if delivery_order_data["delivery_date"] else "",
                    "delivery_method": delivery_order_data["delivery_method"] if delivery_order_data["delivery_method"] else "SF Express",
                    "delivered_order_items": delivery_order_items_data,
                    "delivery_note": delivery_note_sysp["name"] if delivery_note_sysp["name"] else "",
                }
                
                response = {
                    "delivered_data": delivered_data,
                    "role": request.user.role
                }

                return render(request, 'home/after_sales_delivery_details.html', response)
        return render(request, 'home/after_sales_delivery_details.html', {"error_msg": "Delivered order not found.", "role": request.user.role})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/after_sales_delivery_details.html', {"error_msg": str(e), "role": request.user.role})
    
    
@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def save_after_sales_delivery(request):
    try:
        with transaction.atomic():
            if request.method == "POST":
                after_sales_data = json.loads(request.POST.get("after_sales_data"))
                order_type = request.POST.get("order_type")
                delivery_date = request.POST.get("delivery_date")
                delivery_fee = request.POST.get("delivery_fee")
                warehouse_comment = request.POST.get("warehouse_comment")
                order_id = request.POST.get("order_id")
                deliver_id = request.POST.get("deliver_id")

                if order_type:
                    Order.objects.filter(id=order_id).update(order_type=order_type)
                
                order_item_ids = [after_sale["item_id"] for after_sale in after_sales_data]
                if order_item_ids:
                    deliver_order_items = DeliverOrderitems.objects.filter(id__in=order_item_ids).values(
                                                                                            "id",
                                                                                            "order_items_id",
                                                                                            "delivered_quantity",
                                                                                            "order_items__product_id",
                                                                                            )
                    
                    delivery_order = DeliverOrder.objects.filter(id=deliver_id).values("delivery_comments", "delivery_method", "delivery_address").first()
                    delivery_comments = ""
                    delivery_method = "SF Express"
                    delivery_address = ""
                    if delivery_order:
                        delivery_method = delivery_order["delivery_method"] if delivery_order["delivery_method"] else "SF Express"
                        delivery_comments = delivery_order["delivery_comments"] if delivery_order["delivery_comments"] else ""
                        delivery_address = delivery_order["delivery_address"] if delivery_order["delivery_address"] else ""
                    after_sales_deliver_items_obj = []
                    if after_sales_data:
                        after_Sales_deliver_order = DeliverOrder.objects.filter(order_id=order_id, self_deliver_order_id=deliver_id, delivery_id__isnull=True, self_deliver_order__isnull=False).only("id").first()
                        if not after_Sales_deliver_order:
                            after_Sales_deliver_order = DeliverOrder.objects.create(order_id=order_id, 
                                                                        delivery_fee=delivery_fee, 
                                                                        handle_by=request.user,
                                                                        delivery_comments=delivery_comments,
                                                                        delivery_method=delivery_method, 
                                                                        warehouse_comment=warehouse_comment, 
                                                                        delivery_address=delivery_address, 
                                                                        delivery_date=datetime.strptime(str(delivery_date), "%m/%d/%Y").strftime("%Y-%m-%d"),
                                                                        self_deliver_order_id=deliver_id,
                                                                        )
                        for after_sales in after_sales_data:
                            item_id = after_sales["item_id"]
                            failTodeliveryQty = after_sales["failTodeliveryQty"]
                            redeliveryQty = after_sales["redeliveryQty"]
                            overdeliveryQty = after_sales["overdeliveryQty"]
                            returnQty = after_sales["returnQty"]
                            
                            for deliver_order_item in deliver_order_items:
                                if int(deliver_order_item["id"]) == int(item_id):
                                    inventory = Inventory.objects.filter(product_id=deliver_order_item["order_items__product_id"]).only("current_quantity").first()
                                    if inventory:
                                        if failTodeliveryQty:
                                            inventory.current_quantity += int(failTodeliveryQty)
                                        if overdeliveryQty:
                                            inventory.current_quantity -= int(overdeliveryQty)
                                        inventory.save()
                                    
                                    after_sales_deliver_items_obj.append(DeliverOrderitems(
                                        deliver_order_id=after_Sales_deliver_order.id,
                                        order_items_id=deliver_order_item["order_items_id"],
                                        delivered_quantity=deliver_order_item["delivered_quantity"],
                                        failed_delivery_quantity=failTodeliveryQty,
                                        redelivery_quantity=redeliveryQty,
                                        overdelivery_quantity=overdeliveryQty,
                                        return_quantity=returnQty,
                                        self_deliver_order_item_id=deliver_order_item["id"],
                                    ))
                        
                        if after_sales_deliver_items_obj:
                            DeliverOrderitems.objects.bulk_create(after_sales_deliver_items_obj)
                        
                return HttpResponse(json.dumps({"code": 1, "msg": "After sales created successful."}), content_type="json")
            return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@login_required(login_url="/login/")
def after_sales_generate_pdf_for_delivery_note(request, order_id, deliver_id):
    try:
        file_type = "delivery"
        language = "english"
        order_data = Order.objects.filter(id=int(order_id)).first()

        order_item_data = []
        if order_data:
            total_cost = 0
            
            query = Q()
            if deliver_id:
                query.add(Q(id=int(deliver_id)), query.connector)
            else:
                query.add(Q(order_id=int(order_id)) & Q(delivery_id__isnull=True) & Q(self_deliver_order__isnull=False), query.connector)
                
            delivery_order = DeliverOrder.objects.filter(query).first()
            
            if not delivery_order:
                return HttpResponse(json.dumps({"code": 0, "msg": "There's no data for generating after sales delivery note."}), content_type="json") 
            
            deliver_order_items = DeliverOrderitems.objects.filter(deliver_order_id=delivery_order.id)
            # manual_cost = order_data.manual_cost if order_data.manual_cost else 0
            # if order_data.manual_cost:
            #     if (str(order_data.currency).replace("$", "D")).lower() != "hkd":
            #         hkd_manual_discount_price = utils.convert_currency(float(order_data.manual_cost), str(order_data.currency).replace("$", "D"), 'HKD')
            #         if hkd_manual_discount_price:
            #             manual_cost = hkd_manual_discount_price
            
            # order_items = {}
            # for order in deliver_order_items:
            #     if order.redelivery_quantity or order.return_quantity:
            #         if order.order_items_id not in order_items:
            #             order_items[order.order_items_id] = order.delivered_quantity
            #         else:
            #             order_items[order.order_items_id] += order.delivered_quantity
                    
            for order in deliver_order_items:
                # selling_price = order.order_items.selling_price
                # if (str(order_data.currency).replace("$", "D")).lower() != "hkd":
                #     hkd_price = utils.convert_currency(float(selling_price), str(order_data.currency).replace("$", "D"), 'HKD')
                #     if hkd_price:
                #         selling_price = hkd_price
                # subtotal = float(selling_price) * int(order.order_items.quantity)
                # total_cost += subtotal
                if order.redelivery_quantity:
                    delivered_qty = order.redelivery_quantity
                elif order.return_quantity:
                    delivered_qty = '-' + str(order.return_quantity)
                else:
                    delivered_qty = ""
                
                if delivered_qty:
                    inventory = Inventory.objects.filter(product_id=order.order_items.product.id).only("current_quantity").first()
                    if inventory:
                        inventory.current_quantity -= int(delivered_qty)
                        inventory.save()
                    
                order_item_data.append({
                    "code": order.order_items.product.product_id,
                    "product_name": order.order_items.product.product_chinese_name + " " + order.order_items.product.product_english_name,
                    "quantity": order.order_items.quantity,
                    "delivered_quantity": delivered_qty,
                    "remarks": order.order_items.remarks,
                    # "unit_price": round(selling_price, 2),
                    # "subtotal": round(subtotal, 2),
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
            
            delivery_id = delivery_order.delivery_id
            if not delivery_id:
                deliver_order = DeliverOrder.objects.filter(delivery_id__isnull=False).order_by("-id").first()
                number = 10
                delivery_id = "DN" + str(order_data.delivery_date).replace("-", "") + str(number) if order_data.delivery_date else "DN" + str(number)
                if deliver_order and deliver_order.delivery_id:
                    number = int((deliver_order.delivery_id)[10:]) + 1
                    delivery_id = "DN" + str(order_data.delivery_date).replace("-", "") + str(number) if order_data.delivery_date else "DN" + str(number)
                
                new_delivery_id = DeliverOrder.objects.filter(order_id=int(order_id), delivery_id__isnull=True).update(delivery_id=delivery_id, delivery_date=date.today())
            order_data.save()

            bl_base64_with_prefix = ""
            file_path = "apps/static/assets/images/beautiland_logo.png"
            if os.path.exists(file_path):
                with open(file_path, "rb") as file:
                    image_data = file.read()
                    base64_str = base64.b64encode(image_data).decode("utf-8")
                    bl_base64_with_prefix = "data:image/jpeg;base64," + base64_str 
            
            context = {
                "customer_name": order_data.customer.company_english_name if language == "english" else order_data.customer.company_name,
                "address": delivery_order.delivery_address,
                "attention": contact_person,
                "payment": order_data.payment_status if order_data.payment_status else "",
                "delivery_method": order_data.delivery_method if order_data.delivery_method else "",
                "delivery_comments": order_data.customer.delivery_comments,
                "sales_person": sales_person,
                "customer_id": order_data.customer.customer_id,
                "delivery_id": delivery_order.delivery_id if delivery_order.delivery_id else delivery_id,
                "delivery_date": datetime.strptime(str(order_data.delivery_date), "%Y-%m-%d").strftime("%d-%b-%Y") if order_data.delivery_date else "",
                "invoice_id": order_data.order_id,
                "date": datetime.strptime(str(order_data.date), "%Y-%m-%d").strftime("%d-%b-%Y"),
                "telephone": order_data.customer.landline if order_data.customer.landline else "",
                "mobile": mobile,
                "beautiland_logo": bl_base64_with_prefix,
                # "total_cost": round(total_cost - manual_cost, 2) if manual_cost else round(total_cost, 2),
                "order_item_data": order_item_data,
                "blank_space_length": range(15 - len(order_item_data)) if 15 - len(order_item_data) > 0 else range(0),
                "language": language,
                # "manual_discount": round(manual_cost, 2) if manual_cost else 0,
            }
            
            html_string = ""
            file_name = ""
            if file_type == "delivery":
                html_string = render_to_string('home/so_delivery_print.html', context)
                file_name = "delivery_notes_" + order_data.order_id + "_" + delivery_id + "_" + str(datetime.now().date()) + ".pdf"

            if html_string:
                html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
                pdf_file = html.write_pdf()

                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'
                return response
            
        return HttpResponse(json.dumps({"code": 0, "msg": "Order not found."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")
        # return render(request, 'home/order-list.html', {"error_msg": str(e)})
