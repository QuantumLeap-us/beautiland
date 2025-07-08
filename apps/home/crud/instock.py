import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.db.models import Q
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.home.forms.purchaseconfirmationform import ConfirmationForm
from apps.home.forms.purchaseform import PurchaseForm
from apps.home.model.inventory import Inventory
from apps.home.model.purchase_details import Purchase

@login_required(login_url="/login/")
def InstockList(request):
   purchases = Purchase.objects.filter(Q(type='Purchase') & (Q(status='Pending') | Q(status='Partially Delivered')))

   data_arr = []

   for purchase in purchases:
      data_dict = {
         "id": purchase.id,
         "delivery_date": purchase.delivery_date,
         "remarks": purchase.remarks,
         "status":purchase.status,
         "purchaseitems": []
      }

      for purchase_item in purchase.purchase_items.all():
         data_dict['purchaseitems'].append({
            "product_id":purchase_item.product.product_id,
            "product_chinese_name":purchase_item.product.product_chinese_name,
            "supplier_product_name":purchase_item.product.supplier_product_name,
            "purchase_quantity":purchase_item.recommended_purchase_quantity,
            "supplier_name":purchase_item.product.supplier.company_name if purchase_item.product.supplier else  "",
            "supplier_code":purchase_item.product.supplier.supplier_id if purchase_item.product.supplier else "",
            })
         
      data_arr.append(data_dict)
   return render(request, 'home/instock-list.html', { "purchases": data_arr})


@login_required(login_url="/login/")
def InstockGet(request, id):
   form = ConfirmationForm()
   order = Purchase.objects.get(id=id)
   msg=''

   if not order:
      msg = "order not found"
   
   data_dict = {
         "id": order.id,
         "delivery_date": order.delivery_date,
         "remarks": order.remarks,
         "actual_arrival_date":order.actual_arrival_date,
         "status":order.status,
         "purchaseitems": []
      }

   for purchase_item in order.purchase_items.all():
         remaining_quantity = purchase_item.recommended_purchase_quantity - (
            purchase_item.delivered_quantity if purchase_item.delivered_quantity else 0 +
            purchase_item.damage_quantity if purchase_item.damage_quantity else 0)
        
         data_dict['purchaseitems'].append({
            "product_id":purchase_item.product.product_id,
            "product_chinese_name":purchase_item.product.product_chinese_name,
            "product_english_name":purchase_item.product.product_english_name,
            "supplier_product_name":purchase_item.product.supplier_product_name,
            "supplier_name":purchase_item.product.supplier.company_name if purchase_item.product.supplier else  "",
            "supplier_code":purchase_item.product.supplier.supplier_id if purchase_item.product.supplier else  "",
            "purchase_quantity":purchase_item.recommended_purchase_quantity,
            "delivered_quantity":purchase_item.delivered_quantity,
            "damage_quantity":purchase_item.damage_quantity,
            "remaining_quantity":remaining_quantity
            })
   return render(request, 'home/instock-details.html', {"form": form, "order":data_dict, "msg":msg})

@login_required(login_url="/login/")
def InStockDelivery(request, id):
    msg=''
    order = Purchase.objects.get(id=id)
    form = ConfirmationForm()

    if not order:
        msg = "order not found"
        return render(request, 'home/instock.html', {"form": form, "msg":msg})
   
    form = ConfirmationForm(initial={
      'actual_arrival_date':order.actual_arrival_date,
      'status':order.status
    })

    data_dict = {
        "id": order.id,
        "delivery_date": order.delivery_date,
        "remarks": order.remarks,
        "status":order.status,
        "actual_arrival_date":order.actual_arrival_date,
        "purchaseitems": []
    }

    for purchase_item in order.purchase_items.all():
        remaining_quantity = purchase_item.recommended_purchase_quantity - (
            purchase_item.delivered_quantity if purchase_item.delivered_quantity else 0 +
            purchase_item.damage_quantity if purchase_item.damage_quantity else 0)
        
        data_dict['purchaseitems'].append({
            "product_id":purchase_item.product.product_id,
            "product_chinese_name":purchase_item.product.product_chinese_name,
            "product_english_name":purchase_item.product.product_english_name,
            "supplier_product_name":purchase_item.product.supplier_product_name,
            "supplier_name":purchase_item.product.supplier.company_name if purchase_item.product.supplier else  "",
            "supplier_code":purchase_item.product.supplier.supplier_id if purchase_item.product.supplier else  "",
            "purchase_quantity":purchase_item.recommended_purchase_quantity,
            "delivered_quantity":purchase_item.delivered_quantity,
            "damage_quantity":purchase_item.damage_quantity,
            "remaining_quantity":remaining_quantity
        })
         
    if request.method == "POST":

        form = ConfirmationForm(request.POST, instance=order)
      
        form.save()
        # Retrieve delivered and damage quantities from POST data
        quantities = json.loads(request.POST.get('quantity', '{}'))

        with transaction.atomic():
        # products = order.purchase_items.filter(product__product_id=quantity['product_id'])
            for quantity in quantities:
                purchases = order.purchase_items.filter(product__product_id=quantity.get('product_id', ''))
                purchase = purchases.first()
                if quantity['delivered_quantity']!='':
                    purchase.delivered_quantity = quantity['delivered_quantity']
                else:
                    purchase.delivered_quantity = 0
                    quantity['delivered_quantity'] = 0

                if quantity['damage_quantity']!='':
                    purchase.damage_quantity = quantity['damage_quantity']
                else:
                    purchase.damage_quantity = 0
                    quantity['damage_quantity'] = 0

                purchase.save()
                
                product = Inventory.objects.filter(product__product_id=quantity.get('product_id', ''))
                product = product.first()
                product.total_purchased_quantity = product.total_purchased_quantity - (int(quantity['delivered_quantity'])+int(quantity['damage_quantity']))
                product.total_stock_in_quantity = int(quantity['delivered_quantity'])
                product.save()

            msg = _("Purchase information updated successfully")

            return redirect(f"in-stock-get", id=id)

    return render(request, 'home/instock.html', {"form": form, "order": data_dict, "msg": msg})


@login_required(login_url="/login/")
def InstockDelete(request, id):
   msg = ""
   form = PurchaseForm()
   
   purchase = Purchase.objects.filter(id=id)
   purchase.first().purchase_items.all().delete() #deletes the related records
   purchase.delete()
   
   msg = _(f"Purchase deleted successfully")
      
   return redirect("in-stock-list")
   