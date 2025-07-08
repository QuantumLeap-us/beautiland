
from django.shortcuts import redirect, render
from django.db import transaction
from django.contrib.auth.decorators import login_required
# from apps.home.tasks import process_csv_file
from apps.home.models import SystemParameters, SystemParametersForId, Inventory, Product, Supplier, Orderitems
from apps.home.crud import utils, storage_backends, manager
import base64, traceback, json, os
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from apps.home.model.inventory import InventoryPurchaseOrder, InventoryPurchaseOrderItems, StockInOrder, StockMove
from datetime import datetime
from django.db.models import Prefetch
import pandas as pd
from django.http import FileResponse, HttpResponse
from django.db.models import Sum
from django.db.models import OuterRef, Subquery
from apps.home.model.order import DeliverOrderitems


@login_required(login_url="/login/")
def inventoryList(request):
    try:
        inventory_data = []
        inventory_list = Inventory.objects.values(
            "id",
            "product_id",
            "product__product_id",
            "product__product_chinese_name",
            "product__product_english_name",
            "product__category__name",
            "product__sub_category__name",
            "product__unit_of_measurement",
            "product__unit_weight",
            "product__status",
            "current_quantity",
            "product__safe_number",
            "product__supplier__supplier_id",
            "product__supplier__company_name",
            "created_date",
        ).order_by("-created_date")
        
        product_ids = list(inventory_list.values_list("product_id", flat=True))
        product_loss_data = StockMove.objects.filter(product_id__in=product_ids, move_type="Depreciation").values('product_id').annotate(total_quantity=Sum('quantity'))
        latest_order_items = Orderitems.objects.filter(product_id__in=product_ids).filter(
            created_date=Subquery(
                Orderitems.objects.filter(product_id=OuterRef('product_id'))
                .order_by('-created_date')
                .values('created_date')[:1]
            )
        ).values("product_id", "created_date")

        lastest_inventory_po = InventoryPurchaseOrderItems.objects.filter(product_id__in=product_ids).filter(
            created_date=Subquery(
                InventoryPurchaseOrderItems.objects.filter(product_id=OuterRef('product_id'))
                .order_by('-created_date')
                .values('created_date')[:1]
            )
        ).values("product_id", "created_date")
        
        inv_po_items = InventoryPurchaseOrderItems.objects.filter(product_id__in=product_ids).values("product_id").annotate(total_quantity=Sum('quantity'))
        product_id_quantity = {}
        for inv_po_item in inv_po_items:
            product_id_quantity[inv_po_item["product_id"]] = inv_po_item["total_quantity"]

        stockmoves = StockMove.objects.filter(product_id__in=product_ids, stockin_order__inventory_po_item__isnull=False).values("product_id").annotate(total_quantity=Sum('quantity'))
        stockmove_product_id_quantity = {}
        for stockmove in stockmoves:
            stockmove_product_id_quantity[stockmove["product_id"]] = stockmove["total_quantity"]
            
        order_items_data = Orderitems.objects.filter(product_id__in=product_ids).values("id", "product_id")
        order_items_dict = utils.get_dict_from_queryset(order_items_data, "product_id", "id")
        order_items_ids = list(order_items_data.values_list("id", flat=True))
        order_qtys = Orderitems.objects.filter(product_id__in=product_ids).values("product_id").annotate(total_quantity=Sum('quantity'))
        order_items_quantity = {}
        for order_qty in order_qtys:
            order_items_quantity[order_qty["product_id"]] = order_qty["total_quantity"]   
            
        deliver_order_qtys = DeliverOrderitems.objects.filter(order_items_id__in=order_items_ids, self_deliver_order_item_id__isnull=True).values("order_items_id").annotate(total_quantity=Sum('delivered_quantity'))
        # after_sales_deliver_order_qtys = DeliverOrderitems.objects.filter(order_items_id__in=order_items_ids, self_deliver_order_item_id__isnull=False).values("order_items_id", "failed_delivery_quantity", "redelivery_quantity", "overdelivery_quantity", "return_quantity")
        deliver_order_items_quantity = {}
        for deliver_order_qty in deliver_order_qtys:
            deliver_order_items_quantity[deliver_order_qty["order_items_id"]] = deliver_order_qty["total_quantity"]
        
        for inventory in inventory_list:
            total_loss = 0
            for product_loss in product_loss_data:
                if inventory["product_id"] == product_loss["product_id"]:
                    total_loss = product_loss["total_quantity"]

            last_sales_day = "-"
            for latest_order_item in latest_order_items:
                if inventory["product_id"] == latest_order_item["product_id"]:
                    last_sales_day = datetime.strptime(str(latest_order_item["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")

            last_purchase_date = "-"
            for lastest_inventory in lastest_inventory_po:
                if inventory["product_id"] == lastest_inventory["product_id"]:
                    last_purchase_date = datetime.strptime(str(lastest_inventory["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")
            
            qty_tobe_received = 0  
            if product_id_quantity and stockmove_product_id_quantity and inventory["product_id"] in product_id_quantity and inventory["product_id"] in stockmove_product_id_quantity:
                qty_tobe_received = int(product_id_quantity[inventory["product_id"]]) - int(stockmove_product_id_quantity[inventory["product_id"]]) if product_id_quantity[inventory["product_id"]] and stockmove_product_id_quantity[inventory["product_id"]] else 0
            
            delivered_product_qty = 0
            if inventory["product_id"] in order_items_dict:
                order_item_id = order_items_dict[inventory["product_id"]]
                
                # for after_sales in after_sales_deliver_order_qtys:
                #     failed_delivery_quantity = 
                #     redelivery_quantity = 
                #     overdelivery_quantity = 
                #     return_quantity = 
                
                if order_item_id in deliver_order_items_quantity:
                    delivered_product_qty = deliver_order_items_quantity[order_item_id]
            
            current_inventory_after_sales = 0
            current_quantity = inventory["current_quantity"]
            if current_quantity:
                if inventory["product_id"] in order_items_quantity:
                    current_inventory_after_sales = current_quantity - (order_items_quantity[inventory["product_id"]] - delivered_product_qty)
            else:
                current_quantity = "-"
                
            inventory_data.append({
                "created_date": datetime.strptime(str(inventory["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "id": inventory["id"],
                "product_id": inventory["product_id"],
                "product__product_id": inventory["product__product_id"],
                "product_chinese_name": inventory["product__product_chinese_name"] if inventory["product__product_chinese_name"] else "-",
                "product_english_name": inventory["product__product_english_name"] if inventory["product__product_english_name"] else "-",
                "category": inventory["product__category__name"] if inventory["product__category__name"] else "-",
                "sub_category": inventory["product__sub_category__name"] if inventory["product__sub_category__name"] else "-",
                "specification": str(inventory["product__unit_weight"]) + str(inventory["product__unit_of_measurement"]) if inventory["product__unit_weight"] and inventory["product__unit_of_measurement"] else "-",
                "product_status": inventory["product__status"] if inventory["product__status"] else "-",
                "current_quantity": current_quantity,
                "current_inventory_after_sales": current_inventory_after_sales,
                "last_purchase_date": last_purchase_date,
                "qty_tobe_received": qty_tobe_received if qty_tobe_received > 0 else 0,
                "total_loss": total_loss,
                "safe_number": inventory["product__safe_number"] if inventory["product__safe_number"] else "-",
                "supplier_id": inventory["product__supplier__supplier_id"] if inventory["product__supplier__supplier_id"] else "-",
                "supplier_company_name": inventory["product__supplier__company_name"] if inventory["product__supplier__company_name"] else "-",
                "last_sales_day": last_sales_day,
            })

        return render(request, 'home/inventory-list.html', {"inventory_data": inventory_data, "role": request.user.role})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory-list.html', {"error_msg": str(e)})


@login_required(login_url="/login/")
def inventory_purchase_order(request):
    try:
        products = Product.objects.exclude(status="draft").values("id", "product_id", "product_chinese_name", "product_english_name", 
                                          "selling_price", "sales_currency", "unit_of_measurement",
                                          "unit_weight", "purchasing_amount", "supplier__company_name", "total_cost").order_by('-id')
        product_ids = list(products.values_list("id", flat=True))
        inventory_id_stock = {}
        inventory_data = Inventory.objects.filter(product_id__in=product_ids).values("product_id", "current_quantity")
        for inventory in inventory_data:
            if inventory["product_id"] not in inventory_id_stock:
                inventory_id_stock[inventory["product_id"]] = inventory["current_quantity"]
        products_data = []
        for product in products:
            # selling_price = product["selling_price"] if product["selling_price"] else "-"
            # selling_price_with_currency = product["selling_price"]
            # if product["sales_currency"]:
            #     selling_price_with_currency = product["sales_currency"] + " " + str(product["selling_price"])

            #     if (str(product["sales_currency"]).replace("$", "D")).lower() != "hkd":
            #         hkd_price = utils.convert_currency(float(product["selling_price"]), str(product["sales_currency"]).replace("$", "D"), 'HKD')
            #         if hkd_price:
            #             selling_price = hkd_price
            if product["id"] in inventory_id_stock:
                products_data.append({
                    "id": product["id"],
                    "product_id": product["product_id"] if product["product_id"] else "-",
                    "product_chinese_name": product["product_chinese_name"] if product["product_chinese_name"] else "-",
                    "product_english_name": product["product_english_name"] if product["product_english_name"] else "-",
                    "specification":f"{product['unit_weight']} {product['unit_of_measurement']}" if product['unit_weight'] and product["unit_of_measurement"] else "-",
                    "currenct_inventory": inventory_id_stock[product["id"]] if product["id"] in inventory_id_stock and inventory_id_stock[product["id"]] else "0",
                    # "currency": "HKD",
                    "currenct_inventory_after_sales": "",
                    "Last_Purchase_date": "",
                    "suggested_purchase": product["purchasing_amount"] if product["purchasing_amount"] else "",
                    "supplier": product["supplier__company_name"] if product["supplier__company_name"] else "",
                    "total_cost": product["total_cost"] if product["total_cost"] else "",
                })
                
        response = {
            "products_data": products_data,
        }
        return render(request, 'home/inventory_po.html', response)
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory_po.html', {"error_msg": str(e)})
    

@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def create_inventory_purchase_order(request):
    try:
        if request.method == "POST":
            with transaction.atomic():
                product_items_raw = request.POST.get("product_items")
                if not product_items_raw:
                    return HttpResponse(json.dumps({"code": 0, "msg": "Missing product_items"}),
                                        content_type="application/json")

                product_items = json.loads(product_items_raw)
                total_purchase_cost = request.POST.get("total_purchase_cost") or 0
                special_disc = request.POST.get("special_disc") or 0
                total_cost_after_disc = request.POST.get("total_cost_after_disc") or 0
                button = request.POST.get("button", "").lower()

                total_quantity = 0
                inv_po_items_obj = []

                for product_item in product_items:
                    product = Inventory.objects.filter(
                        product_id=int(product_item["product_id"])
                    ).values(
                        "current_quantity", "product_id",
                        "product__currency_of_cost", "product__supplier_id",
                        "product__product_chinese_name"
                    ).first()

                    if not product:
                        return HttpResponse(json.dumps({
                            "code": 0,
                            "msg": f"Product ID {product_item['product_id']} not found."
                        }), content_type="application/json")

                    total_quantity += int(product_item["qty"])

                    item = InventoryPurchaseOrderItems(
                        product_id=int(product_item["product_id"]),
                        item_name_chinese=product_item["prod_chinese_name"],
                        item_name_english=product_item["prod_english_name"],
                        item_specification=product_item["prod_spec"],
                        item_currency=product["product__currency_of_cost"],
                        supplier_id=product["product__supplier_id"],
                        supplier_name=product_item["prod_supplier"],
                        purchase_cost=product_item["purchase_cost"],
                        quantity=product_item["qty"],
                        subtotal=product_item["subtotal"],
                        remark=product_item["remark"],
                        status="Draft" if button == "save" else "Pending Stock In",
                    )
                    item.save()  # 改为 save()，避免 bulk_create 造成 .add() 失败
                    inv_po_items_obj.append(item)

                # 创建主订单
                inv_po = InventoryPurchaseOrder.objects.values("inventory_po_id").order_by("-id").first()
                current_date = datetime.now()
                formatted_date = current_date.strftime("%Y%m%d")
                inventory_po_id = f"PO{formatted_date}10"
                if inv_po:
                    try:
                        seq = int(inv_po["inventory_po_id"][10:]) + 1
                        inventory_po_id = f"PO{formatted_date}{seq}"
                    except:
                        pass  # 防止旧数据格式错误

                inventory_po_obj = InventoryPurchaseOrder.objects.create(
                    inventory_po_id=inventory_po_id,
                    total_quantity=total_quantity,
                    total_purchase_cost=total_purchase_cost,
                    special_disocunt=special_disc,
                    total_cost=total_cost_after_disc,
                )

                # 添加 M2M 关系
                inventory_po_obj.inventory_purchase_items.add(*inv_po_items_obj)
                inventory_po_obj.save()

            return HttpResponse(json.dumps({"code": 1, "msg": "Success!"}), content_type="application/json")

        return HttpResponse(json.dumps({"code": 0, "msg": "Invalid request method"}), content_type="application/json")

    except Exception as e:
        print("异常：", str(e))
        print(traceback.format_exc())
        try:
            manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        except Exception:
            pass  # 保证即使 manager 报错也能返回
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="application/json")
    

@login_required(login_url="/login/")
def inventory_purchase_order_list(request):
    try:
        inventory_po_data = []
        inventory_pos = InventoryPurchaseOrder.objects.filter(is_deleted=False).prefetch_related(
            Prefetch(
                'inventory_purchase_items',
                queryset=InventoryPurchaseOrderItems.objects.all(),
                to_attr='purchase_items'
            )
        ).order_by("-id")

        for inv_po in inventory_pos:
            purchase_items = inv_po.purchase_items
            for item in purchase_items:
                actual_arrival_qty = StockMove.objects.filter(stockin_order__inventory_po_item_id=item.id, product_id=item.product_id, move_type__in=["purchase", "Purchase"]).aggregate(total_quantity=Sum('quantity'))
                inventory_po_data.append({
                    "created_date": datetime.strptime(str(inv_po.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                    "inv_po_id": inv_po.id,
                    "inventory_po_id": inv_po.inventory_po_id,
                    "status": item.status,
                    "product_id": item.product_id,
                    "product__product_id": item.product.product_id,
                    "item_name_chinese": item.item_name_chinese if item.item_name_chinese else "-",
                    "item_name_english": item.item_name_english if item.item_name_english else "-",
                    "item_specification": item.item_specification if item.item_specification else "-",
                    "item_currency": item.item_currency if item.item_currency else "-",
                    "supplier_id": item.supplier_id if item.supplier_id else "-",
                    "supplier__supplier_id": item.supplier.supplier_id if item.supplier.supplier_id else "-",
                    "supplier_name": item.supplier.company_name if item.supplier.company_name else "-",
                    "purchase_cost": item.purchase_cost if item.purchase_cost else "-",
                    "quantity": item.quantity if item.quantity else "-",
                    "subtotal": item.subtotal if item.subtotal else "-",
                    "remark": item.remark if item.remark else "-",
                    "expected_arrival_date": str(inv_po.expected_arrival_date) if inv_po.expected_arrival_date else "-",
                    "actual_arrival_quantity": actual_arrival_qty["total_quantity"] if actual_arrival_qty["total_quantity"] else "-",
                })
                
        response = {
            "inventory_po_data": inventory_po_data,
        }
        return render(request, 'home/inventory_po_list.html', response)
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory_po_list.html', {"error_msg": str(e)})
    

@login_required(login_url="/login/")
def inventory_purchase_order_details(request, inv_po_id):
    try:
        inventory_po_data = []
        inventory_pos = InventoryPurchaseOrder.objects.filter(id=inv_po_id, is_deleted=False).prefetch_related(
            Prefetch(
                'inventory_purchase_items',
                queryset=InventoryPurchaseOrderItems.objects.all(),
                to_attr='purchase_items'
            )
        ).order_by("-id").first()

        if inventory_pos:
            status = ""
            purchase_items = inventory_pos.purchase_items
            for item in purchase_items:
                status = item.status
                inventory_po_data.append({
                    "item_id": item.id,
                    "created_date": datetime.strptime(str(inventory_pos.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                    "inventory_po_id": inventory_pos.inventory_po_id,
                    "status": item.status,
                    "product_id": item.product_id,
                    "product__product_id": item.product.product_id,
                    "item_name_chinese": item.item_name_chinese if item.item_name_chinese else "-",
                    "item_name_english": item.item_name_english if item.item_name_english else "-",
                    "item_specification": item.item_specification if item.item_specification else "-",
                    "item_currency": item.item_currency if item.item_currency else "-",
                    "supplier_id": item.supplier_id if item.supplier_id else "-",
                    "supplier__supplier_id": item.supplier.supplier_id if item.supplier.supplier_id else "-",
                    "supplier_name": item.supplier.company_name if item.supplier.company_name else "-",
                    "purchase_cost": item.purchase_cost if item.purchase_cost else "",
                    "quantity": item.quantity if item.quantity else "",
                    "subtotal": item.subtotal if item.subtotal else "",
                    "remark": item.remark if item.remark else "",
                })
                
        response = {
            "inventory_po_data": inventory_po_data,
            "inv_po_id": inventory_pos.id,
            "expected_arrival_date": str(inventory_pos.expected_arrival_date) if inventory_pos.expected_arrival_date else "",
            "delivery_fee": inventory_pos.delivery_fee if inventory_pos.delivery_fee else "",
            "total_purchase_cost": inventory_pos.total_purchase_cost if inventory_pos.total_purchase_cost else "",
            "special_discount": inventory_pos.special_disocunt if inventory_pos.special_disocunt else "",
            "total_cost_after_discount": inventory_pos.total_cost if inventory_pos.total_cost else "",
            "status": status,
        }

        return render(request, 'home/inventory_po_details.html', response)
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory_po_details.html', {"error_msg": str(e)})
    

@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def update_inventory_purchase_order(request):
    try:
        if request.method == "POST":
            with transaction.atomic():
                product_items = json.loads(request.POST.get("product_items")) if request.POST.get("product_items") else []
                total_purchase_cost = request.POST.get("total_purchase_cost")
                special_disc = request.POST.get("special_disc")
                total_cost_after_disc = request.POST.get("total_cost_after_disc")
                inv_po_id = request.POST.get("inv_po_id")
                expected_arrival_date = request.POST.get("expected_arrival_date")
                delivery_fee = request.POST.get("delivery_fee")
                button = request.POST.get("button")
                
                total_quantity = 0
                inv_po_items_obj = []
                # qty_errors = []
                for product_item in product_items:
                    product = Inventory.objects.filter(product_id=int(product_item["product_id"])).values("current_quantity", "product_id", "product__currency_of_cost", "product__supplier_id", "product__product_chinese_name").first()
                    if product:
                        # if int(product_item["qty"]) > int(product["current_quantity"]):
                        #     qty_errors.append("Quantity can not be greater than <b>" + str(product["current_quantity"]) + "</b> for product <b>" + str(product["product__product_chinese_name"]) + "</b>.")
                            
                        total_quantity += int(product_item["qty"])
                        
                        item_status = InventoryPurchaseOrderItems.objects.filter(id=int(product_item["item_id"])).values("status", "quantity").first()
                        status = item_status["status"]
                        if str(status).lower() == "draft" and button == "save":
                            status = "Draft"
                        elif str(status).lower() == "draft" and button == "submit":
                            status = "Pending Stock In"
                            
                        total_po_item_quantity = StockMove.objects.filter(stockin_order__inventory_po_item_id=int(product_item["item_id"])).aggregate(total_quantity=Sum('quantity'))
                        if total_po_item_quantity and total_po_item_quantity["total_quantity"] and item_status["quantity"]:
                            if int(total_po_item_quantity["total_quantity"]) == int(item_status["quantity"]):
                                status = "Pending Stock In"

                        inv_po_items_obj.append({
                            "id":int(product_item["item_id"]),
                            "purchase_cost": product_item["purchase_cost"],
                            "quantity": product_item["qty"],
                            "subtotal": product_item["subtotal"],
                            "remark": product_item["remark"],
                            "status": status,
                        })

                # if qty_errors:
                #     return HttpResponse(json.dumps({"code": 0, "msg": ", ".join(qty_errors)}), content_type="json")

                if inv_po_items_obj:
                    InventoryPurchaseOrderItems.objects.bulk_update([InventoryPurchaseOrderItems(**kv) for kv in inv_po_items_obj], ["purchase_cost", "quantity", "subtotal", "remark", "status"])   
                
                inventory_po_obj = InventoryPurchaseOrder.objects.filter(id=inv_po_id).first()
                if inventory_po_obj:
                    # status = inventory_po_obj.status
                    # if str(status).lower() == "draft" and button == "save":
                    #     status = "Draft"
                    # elif str(status).lower() == "draft" and button == "submit":
                    #     status = "Pending Stock In"
                    inventory_po_obj.total_quantity=total_quantity
                    inventory_po_obj.total_purchase_cost=total_purchase_cost
                    inventory_po_obj.special_disocunt=special_disc
                    inventory_po_obj.total_cost=total_cost_after_disc
                    # inventory_po_obj.status=status
                    inventory_po_obj.expected_arrival_date=datetime.strptime(str(expected_arrival_date), "%m/%d/%Y") if expected_arrival_date else None
                    inventory_po_obj.delivery_fee=delivery_fee
                    inventory_po_obj.save()
                else:    
                    return HttpResponse(json.dumps({"code": 0, "msg": "Inventory purchase order does not exist."}), content_type="json")
            return HttpResponse(json.dumps({"code": 1, "msg": "Success!"}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    

@login_required(login_url="/login/")
def inventory_list_export(request):
    try:
        inventory_data = []
        inventory_list = Inventory.objects.values(
            "id",
            "product_id",
            "product__product_id",
            "product__product_chinese_name",
            "product__product_english_name",
            "product__category__name",
            "product__sub_category__name",
            "product__unit_of_measurement",
            "product__unit_weight",
            "product__status",
            "current_quantity",
            "product__safe_number",
            "product__supplier__supplier_id",
            "product__supplier__company_name",
            "created_date",
        ).order_by("-created_date")
        
        product_ids = list(inventory_list.values_list("product_id", flat=True))
        product_loss_data = StockMove.objects.filter(product_id__in=product_ids, move_type="Depreciation").values('product_id').annotate(total_quantity=Sum('quantity'))
        latest_order_items = Orderitems.objects.filter(product_id__in=product_ids).filter(
            created_date=Subquery(
                Orderitems.objects.filter(product_id=OuterRef('product_id'))
                .order_by('-created_date')
                .values('created_date')[:1]
            )
        ).values("product_id", "created_date")

        lastest_inventory_po = InventoryPurchaseOrderItems.objects.filter(product_id__in=product_ids).filter(
            created_date=Subquery(
                InventoryPurchaseOrderItems.objects.filter(product_id=OuterRef('product_id'))
                .order_by('-created_date')
                .values('created_date')[:1]
            )
        ).values("product_id", "created_date")
        
        inv_po_items = InventoryPurchaseOrderItems.objects.filter(product_id__in=product_ids).values("product_id").annotate(total_quantity=Sum('quantity'))
        product_id_quantity = {}
        for inv_po_item in inv_po_items:
            product_id_quantity[inv_po_item["product_id"]] = inv_po_item["total_quantity"]
        stockmoves = StockMove.objects.filter(product_id__in=product_ids).values("product_id").annotate(total_quantity=Sum('quantity'))
        stockmove_product_id_quantity = {}
        for stockmove in stockmoves:
            stockmove_product_id_quantity[stockmove["product_id"]] = stockmove["total_quantity"] 
        
        for inventory in inventory_list:
            total_loss = 0
            for product_loss in product_loss_data:
                if inventory["product_id"] == product_loss["product_id"]:
                    total_loss = product_loss["total_quantity"]

            last_sales_day = ""
            for latest_order_item in latest_order_items:
                if inventory["product_id"] == latest_order_item["product_id"]:
                    last_sales_day = datetime.strptime(str(latest_order_item["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")

            last_purchase_date = ""
            for lastest_inventory in lastest_inventory_po:
                if inventory["product_id"] == lastest_inventory["product_id"]:
                    last_purchase_date = datetime.strptime(str(lastest_inventory["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d")
            
            qty_tobe_received = 0  
            if product_id_quantity and stockmove_product_id_quantity and inventory["product_id"] in product_id_quantity and inventory["product_id"] in stockmove_product_id_quantity:
                qty_tobe_received = int(product_id_quantity[inventory["product_id"]]) - int(stockmove_product_id_quantity[inventory["product_id"]]) if product_id_quantity[inventory["product_id"]] and stockmove_product_id_quantity[inventory["product_id"]] else 0
                
            inventory_data.append({
                "Created Date": datetime.strptime(str(inventory["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "Product ID": inventory["product__product_id"],
                "Name": inventory["product__product_chinese_name"] if inventory["product__product_chinese_name"] else "",
                "English Name": inventory["product__product_english_name"] if inventory["product__product_english_name"] else "",
                "Main Category": inventory["product__category__name"] if inventory["product__category__name"] else "",
                "Sub Category": inventory["product__sub_category__name"] if inventory["product__sub_category__name"] else "",
                "Specification": str(inventory["product__unit_weight"]) + str(inventory["product__unit_of_measurement"]) if inventory["product__unit_weight"] and inventory["product__unit_of_measurement"] else "",
                "Status": inventory["product__status"] if inventory["product__status"] else "",
                "Current Inventory Quantity": inventory["current_quantity"] if inventory["current_quantity"] else "",
                "Current Inventory Quantity After Sales": 0,
                "Last Purchase Date": last_purchase_date,
                "Quantity to be Received": qty_tobe_received if qty_tobe_received > 0 else 0,
                "Total Loss": total_loss,
                "Recommended Purchase Quantity": inventory["product__safe_number"] if inventory["product__safe_number"] else "",
                "Supplier ID": inventory["product__supplier__supplier_id"] if inventory["product__supplier__supplier_id"] else "",
                "Supplier Name": inventory["product__supplier__company_name"] if inventory["product__supplier__company_name"] else "",
                "Last Sales Day": last_sales_day,
            })

        df = pd.DataFrame(inventory_data)

        now = datetime.now().strftime("%d%m%Y")
        file_path = 'media/temp/inventory/' + str(request.user.id) + "/"
        file_name = "inventory_" + str(now) + ".xlsx"
        full_file_path = file_path + file_name
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        df.to_excel(full_file_path, index=False)        

        response = FileResponse(open(full_file_path, 'rb'), content_type='text/xlsx')
        response['Content-Disposition'] = f'attachment; filename=' + file_name
        return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory-list.html', {"error_msg": str(e)})
    

"""""""""""""""""""""""""Inventory - stock manage"""""""""""""""""""""""""

@login_required(login_url="/login/")
def inventory_stockin_list(request):
    try:
        stockin_order_data = []
        stockin_order_list = StockMove.objects.values(
            "id",
            "stockin_order__stockin_order_id",
            "stockin_order__inventory_po_item_id",
            "stockin_order__inventory_po_item__item_name_chinese",
            "stockin_order__inventory_po_item__item_name_english",
            "product__product_id",
            "stockin_order__inventory_po_item__quantity",
            "quantity",
            "remark",
            "created_date",
            "move_type",
            "stockin_order__staff__first_name",
            "stockin_order__staff__last_name",
        ).order_by("-created_date")
        
        inv_po_items_ids = list(stockin_order_list.values_list("stockin_order__inventory_po_item_id", flat=True))
        inv_po = InventoryPurchaseOrder.objects.filter(inventory_purchase_items__in=inv_po_items_ids).values("inventory_po_id", "inventory_purchase_items")
        inv_po_item_id_po_id = utils.get_dict_from_queryset(inv_po, "inventory_purchase_items", "inventory_po_id")
        
        for stockin_order in stockin_order_list:
            staff_name = utils.get_user_full_name(stockin_order["stockin_order__staff__first_name"], stockin_order["stockin_order__staff__last_name"])
            stockin_order_data.append({
                "id": stockin_order["id"],
                "created_date": datetime.strptime(str(stockin_order["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "type": stockin_order["move_type"] if stockin_order["move_type"] else "-",
                "stockin_order_id": stockin_order["stockin_order__stockin_order_id"] if stockin_order["stockin_order__stockin_order_id"] else "-",
                "purchase_order_id": inv_po_item_id_po_id[stockin_order["stockin_order__inventory_po_item_id"]] if stockin_order["stockin_order__inventory_po_item_id"] in inv_po_item_id_po_id else "-",
                "product__product_id": stockin_order["product__product_id"],
                "product_chinese_name": stockin_order["stockin_order__inventory_po_item__item_name_chinese"] if stockin_order["stockin_order__inventory_po_item__item_name_chinese"] else "-",
                "product_english_name": stockin_order["stockin_order__inventory_po_item__item_name_english"] if stockin_order["stockin_order__inventory_po_item__item_name_english"] else "-",
                "expected_stock_in_qty": stockin_order["stockin_order__inventory_po_item__quantity"] if stockin_order["stockin_order__inventory_po_item__quantity"] else 0,
                "depreciation": stockin_order["quantity"] if str(stockin_order["move_type"]).lower() == "depreciation" else "-",
                "actual_stock_in": stockin_order["quantity"] if str(stockin_order["move_type"]).lower() != "depreciation" else "-",
                "staff": staff_name if staff_name else "-",
                "stock_in_remark": stockin_order["remark"] if stockin_order["remark"] else "-",
            })

        return render(request, 'home/inventory-stockin-list.html', {"stockin_order_data": stockin_order_data, "role": request.user.role})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory-stockin-list.html', {"error_msg": str(e)})
    

@login_required(login_url="/login/")
def inventory_stockin_list_export(request):
    try:
        stockin_order_data = []
        stockin_order_list = StockMove.objects.values(
            "id",
            "stockin_order__stockin_order_id",
            "stockin_order__inventory_po_item_id",
            "stockin_order__inventory_po_item__item_name_chinese",
            "stockin_order__inventory_po_item__item_name_english",
            "product__product_id",
            "stockin_order__inventory_po_item__quantity",
            "quantity",
            "remark",
            "created_date",
            "move_type",
            "stockin_order__staff__first_name",
            "stockin_order__staff__last_name",
        ).order_by("-created_date")
        
        inv_po_items_ids = list(stockin_order_list.values_list("stockin_order__inventory_po_item_id", flat=True))
        inv_po = InventoryPurchaseOrder.objects.filter(inventory_purchase_items__in=inv_po_items_ids).values("inventory_po_id", "inventory_purchase_items")
        inv_po_item_id_po_id = utils.get_dict_from_queryset(inv_po, "inventory_purchase_items", "inventory_po_id")
        
        for stockin_order in stockin_order_list:
            staff_name = utils.get_user_full_name(stockin_order["stockin_order__staff__first_name"], stockin_order["stockin_order__staff__last_name"])
            stockin_order_data.append({
                "Stock In Date": datetime.strptime(str(stockin_order["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                "Type": stockin_order["move_type"] if stockin_order["move_type"] else "",
                "Stock In ID": stockin_order["stockin_order__stockin_order_id"] if stockin_order["stockin_order__stockin_order_id"] else "",
                "Purchase Order ID": inv_po_item_id_po_id[stockin_order["stockin_order__inventory_po_item_id"]] if stockin_order["stockin_order__inventory_po_item_id"] in inv_po_item_id_po_id else "",
                "Product ID": stockin_order["product__product_id"],
                "Name": stockin_order["stockin_order__inventory_po_item__item_name_chinese"] if stockin_order["stockin_order__inventory_po_item__item_name_chinese"] else "",
                "English Name": stockin_order["stockin_order__inventory_po_item__item_name_english"] if stockin_order["stockin_order__inventory_po_item__item_name_english"] else "",
                "Expected Stock In Quantity": stockin_order["stockin_order__inventory_po_item__quantity"] if stockin_order["stockin_order__inventory_po_item__quantity"] else 0,
                "Depreciation": stockin_order["quantity"] if str(stockin_order["move_type"]).lower() == "depreciation" else "",
                "Actual Stock In": stockin_order["quantity"] if str(stockin_order["move_type"]).lower() != "depreciation" else "",
                "Staff": staff_name if staff_name else "",
                "Remark": stockin_order["remark"] if stockin_order["remark"] else "",
            })

        df = pd.DataFrame(stockin_order_data)

        now = datetime.now().strftime("%d%m%Y")
        file_path = 'media/temp/inventory_stockin/' + str(request.user.id) + "/"
        file_name = "inventory_stockin_" + str(now) + ".xlsx"
        full_file_path = file_path + file_name
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        df.to_excel(full_file_path, index=False)        

        response = FileResponse(open(full_file_path, 'rb'), content_type='text/xlsx')
        response['Content-Disposition'] = f'attachment; filename=' + file_name
        return response
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory-stockin-list.html', {"error_msg": str(e)})


@login_required(login_url="/login/")
def inventory_stockin_order(request):
    try:
        inventory_po_data = []
        inventory_pos = InventoryPurchaseOrder.objects.filter(is_deleted=False).prefetch_related(
            Prefetch(
                'inventory_purchase_items',
                queryset=InventoryPurchaseOrderItems.objects.exclude(status__in=["Stocked In", "Draft"]).all(),
                to_attr='purchase_items'
            )
        ).order_by("-id")

        for inventory_po in inventory_pos:
            purchase_items = inventory_po.purchase_items
            for item in purchase_items:
                total_quantity = StockMove.objects.filter(stockin_order__inventory_po_item_id=item.id).aggregate(total_quantity=Sum('quantity'))
                quantity = item.quantity if item.quantity else ""
                if total_quantity:
                    quantity = item.quantity - total_quantity['total_quantity'] if item.quantity and total_quantity['total_quantity'] else item.quantity
                if quantity > 0:
                    inventory_po_data.append({
                        "item_id": item.id,
                        "created_date": datetime.strptime(str(inventory_po.created_date), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
                        "inventory_po_id": inventory_po.inventory_po_id,
                        "product_id": item.product_id,
                        "product__product_id": item.product.product_id,
                        "item_name_chinese": item.item_name_chinese if item.item_name_chinese else "-",
                        "item_name_english": item.item_name_english if item.item_name_english else "-",
                        "item_specification": item.item_specification if item.item_specification else "-",
                        "quantity": quantity,
                        "inv_po_id": inventory_po.id,
                    })
                
        response = {
            "inventory_po_data": inventory_po_data,
        }
        return render(request, 'home/inventory_stockin_order.html', response)
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory_stockin_order.html', {"error_msg": str(e)})
    

@method_decorator(csrf_exempt, name='dispatch')
@login_required(login_url="/login/")
def create_inventory_stockin(request):
    try:
        if request.method == "POST":
            with transaction.atomic():
                product_items = eval(request.POST.get("product_items")) if request.POST.get("product_items") else []                

                for prod_item in product_items:
                    latest_stockin_order = StockInOrder.objects.values("stockin_order_id").order_by("-id").first()
                    current_date = datetime.now()
                    formatted_date = current_date.strftime("%Y%m%d")
                    stockin_order_id = f"SI{formatted_date}11"
                    if latest_stockin_order:
                        seq = int(latest_stockin_order["stockin_order_id"][10:]) + 1
                        stockin_order_id = f"SI{formatted_date}{seq}"  

                    # stock_in_order = StockInOrder.objects.filter(inventory_po_item_id=int(prod_item["item_id"])).first()
                    # if stock_in_order:
                    #     stock_in_order.depreciation += prod_item["depreciation"]
                    #     stock_in_order.actual_stock_in += prod_item["actual_stock_in"]
                    #     stock_in_order.stock_in_remark = prod_item["stock_in_remark"]
                    #     stock_in_order.save()
                    # else:
                    stock_in_order = StockInOrder.objects.create(
                            stockin_order_id=stockin_order_id,
                            inventory_po_item_id=int(prod_item["item_id"]),
                            # depreciation=prod_item["depreciation"],
                            # actual_stock_in=prod_item["actual_stock_in"],
                            # stock_in_remark=prod_item["stock_in_remark"],
                            staff_id=request.user.id,
                        )

                    if prod_item["depreciation"] and int(prod_item["depreciation"]) > 0:
                        StockMove.objects.create(product_id=prod_item["product_id"], move_type="Depreciation", remark=prod_item["stock_in_remark"], quantity=int(prod_item["depreciation"]), stockin_order_id=stock_in_order.id)
                    if prod_item["actual_stock_in"] and int(prod_item["actual_stock_in"]) > 0:
                        StockMove.objects.create(product_id=prod_item["product_id"], move_type="Purchase", remark=prod_item["stock_in_remark"], quantity=int(prod_item["actual_stock_in"]), stockin_order_id=stock_in_order.id)

                    inventory = Inventory.objects.filter(product_id=prod_item["product_id"]).first()
                    if inventory:
                        inventory.current_quantity += int(prod_item["actual_stock_in"])
                        inventory.save()
                    
                    inv_po_item = InventoryPurchaseOrderItems.objects.filter(id=int(prod_item["item_id"])).first()
                    if inv_po_item:
                        total_quantity = StockMove.objects.filter(stockin_order__inventory_po_item_id=int(prod_item["item_id"])).aggregate(total_quantity=Sum('quantity'))
                        if int(total_quantity["total_quantity"]) == int(inv_po_item.quantity):
                            inv_po_item.status = "Stocked In"
                            inv_po_item.save()
            return HttpResponse(json.dumps({"code": 1, "msg": "Success!"}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")


@login_required(login_url="/login/")
def inventory_edit_stockin_order(request, id):
    try:
        if request.method == "POST":
            with transaction.atomic():
                if id:
                    inv_type = request.POST.get("type")
                    product_id = request.POST.get("product_id")
                    old_quantity = request.POST.get("old_quantity")
                    quantity = request.POST.get("quantity")
                    remark = request.POST.get("remark")
                    
                    stock_move = StockMove.objects.filter(id=id).first()
                    if stock_move:
                        specification = str(stock_move.product.unit_weight) + " " + str(stock_move.product.unit_of_measurement) if stock_move.product.unit_weight and stock_move.product.unit_of_measurement else ""
                        chinese_name = stock_move.stockin_order.inventory_po_item.item_name_chinese if stock_move.stockin_order.inventory_po_item else ""
                        if not chinese_name:
                            chinese_name = stock_move.product.product_chinese_name if stock_move.product.product_chinese_name else ""
                        english_name = stock_move.stockin_order.inventory_po_item.item_name_english if stock_move.stockin_order.inventory_po_item else ""
                        if not english_name:
                            english_name = stock_move.product.product_english_name if stock_move.product.product_english_name else ""
                        stockmove_data = {"product_id": stock_move.product.product_id, 
                                        "move_type": stock_move.move_type, 
                                        "remark": stock_move.remark, 
                                        "quantity": stock_move.quantity, 
                                        "id": id, 
                                        "chinese_name": chinese_name,
                                        "english_name": english_name,
                                        "specification": specification,
                                        "error_msg": "<b>Quantity</b> and <b>Type</b> fields are mandatory, <b>Quantity</b> must not be 0."
                                        }

                        if not quantity and int(quantity) == 0 or not inv_type:
                            return render(request, 'home/inventory_edit_stockin_order.html', stockmove_data)

                        stock_move.move_type = inv_type 
                        stock_move.quantity = quantity
                        stock_move.remark = remark
                        stock_move.save()
                        
                        diff = int(quantity) - int(old_quantity)
                        inventory = Inventory.objects.filter(product_id=stock_move.product.id).first()
                        if inventory:
                            inventory.current_quantity += int(diff)
                            if inventory.current_quantity < 0:
                                stockmove_data["error_msg"] = "Product <b>" + stock_move.product.product_id + "</b> quantity cannot be negetive."
                                return render(request, 'home/inventory_edit_stockin_order.html', stockmove_data)
                            inventory.save()
                            
                        return redirect("inventory_stockin_list")
                    return render(request, 'home/inventory_edit_stockin_order.html', {"error_msg": "Data not found."})
                else:
                    latest_stockin_order = StockInOrder.objects.values("stockin_order_id").order_by("-id").first()
                    current_date = datetime.now()
                    formatted_date = current_date.strftime("%Y%m%d")
                    stockin_order_id = f"SI{formatted_date}11"
                    if latest_stockin_order:
                        seq = int(latest_stockin_order["stockin_order_id"][10:]) + 1
                        stockin_order_id = f"SI{formatted_date}{seq}"  

                    for i in range(1, 9):
                        if request.POST.get("quantity_" + str(i)) and int(request.POST.get("quantity_" + str(i))) != 0 and request.POST.get("type_" + str(i)):  
                            inv_type = request.POST.get("type_" + str(i))
                            product_id = request.POST.get("product_id_" + str(i))
                            quantity = request.POST.get("quantity_" + str(i))
                            remark = request.POST.get("remark_" + str(i))
                            
                            stock_in_order = StockInOrder.objects.create(
                                    stockin_order_id=stockin_order_id,
                                    inventory_po_item_id="",
                                    staff_id=request.user.id,
                                )

                            product = Product.objects.filter(product_id=product_id).values("id").first()
                            if product:
                                StockMove.objects.create(product_id=product["id"], move_type=inv_type, remark=remark, quantity=int(quantity), stockin_order_id=stock_in_order.id)

                                inventory = Inventory.objects.filter(product_id=product["id"]).first()
                                if inventory:
                                    inventory.current_quantity += int(quantity)
                                    inventory.save()
                            
                return redirect("inventory_stockin_list")
        else:
            stockmove_data = {"id": id}
            if id:
                stockmove = StockMove.objects.filter(id=id).values("product__product_id", "product__product_chinese_name", "product__product_english_name", "move_type", "remark", "quantity", "stockin_order__inventory_po_item__item_name_chinese", "stockin_order__inventory_po_item__item_name_english", "product__unit_weight", "product__unit_of_measurement").first()
                if stockmove:
                    specification = str(stockmove["product__unit_weight"]) + " " + str(stockmove["product__unit_of_measurement"]) if stockmove["product__unit_weight"] and stockmove["product__unit_of_measurement"] else ""
                    chinese_name = stockmove["stockin_order__inventory_po_item__item_name_chinese"] if stockmove["stockin_order__inventory_po_item__item_name_chinese"] else ""
                    if not chinese_name:
                        chinese_name = stockmove["product__product_chinese_name"] if stockmove["product__product_chinese_name"] else ""
                    english_name = stockmove["stockin_order__inventory_po_item__item_name_english"] if stockmove["stockin_order__inventory_po_item__item_name_english"] else ""
                    if not english_name:
                        english_name = stockmove["product__product_english_name"] if stockmove["product__product_english_name"] else ""
                    stockmove_data = {"product_id": stockmove["product__product_id"], 
                                      "move_type": stockmove["move_type"], 
                                      "remark": stockmove["remark"], 
                                      "quantity": stockmove["quantity"], 
                                      "id": id, 
                                      "chinese_name": chinese_name,
                                      "english_name": english_name,
                                      "specification": specification,
                                      }
            return render(request, 'home/inventory_edit_stockin_order.html', stockmove_data)
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, 'home/inventory_edit_stockin_order.html', {"error_msg": "Something went wrong."})
    

@login_required(login_url="/login/")
def get_product(request, product_id):
    try:
        product_data = {}
        product = Product.objects.filter(product_id=product_id).values("product_chinese_name", "product_english_name", "unit_of_measurement", "unit_weight").first()
        if product:
            specification = str(product["unit_weight"]) + " " + str(product["unit_of_measurement"]) if product["unit_weight"] and product["unit_of_measurement"] else ""
            product_data = {"product_chinese_name": product["product_chinese_name"], "product_english_name": product["product_english_name"], "specification": specification}

            return HttpResponse(json.dumps({"code": 1, "product_data": product_data}), content_type="json")
        return HttpResponse(json.dumps({"code": 0, "msg": "Product <b>" + str(product_id) + "</b> does not exist."}), content_type="json")
    except Exception as e:    
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": "Something went wrong."}), content_type="json")
