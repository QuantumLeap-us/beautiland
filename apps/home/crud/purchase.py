import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import transaction
from datetime import datetime, timedelta
from django.utils.translation import gettext_lazy as _
from django.db.models import F 

from apps.home.forms.purchaseform import PurchaseForm
from apps.home.forms.purchaseconfirmationform import ConfirmationForm
from apps.home.model.inventory import Inventory
from apps.home.models import Product, Purchase, PurchaseItems


@login_required(login_url="/login/")
def purchaseList(request):
   form = PurchaseForm()
   purchases = Purchase.objects.filter(type="Purchase")

   data_arr = []

   for purchase in purchases:
      data_dict = {
         "id": purchase.id,
         "delivery_date": purchase.delivery_date,
         "delivery_cost": purchase.delivery_cost,
         "total_cost": purchase.total_cost,
         "payment_method": purchase.payment_method,
         "remarks": purchase.remarks,
         "status":purchase.status,
         "purchaseitems": []
      }

      for purchase_item in purchase.purchase_items.all():
         data_dict['purchaseitems'].append({
            "product_id":purchase_item.product.product_id,
            "product_chinese_name":purchase_item.product.product_chinese_name,
            "product_english_name":purchase_item.product.product_english_name,
            "supplier_product_name":purchase_item.product.supplier_product_name,
            "sub_total":purchase_item.total_cost,
            "purchase_quantity":purchase_item.recommended_purchase_quantity,
            "supplier_name":purchase_item.product.supplier.company_name if purchase_item.product.supplier else "",
            "supplier_code":purchase_item.product.supplier.supplier_id if purchase_item.product.supplier else "",
            })
         
      data_arr.append(data_dict)
   return render(request, 'home/purchase-list.html', {"form": form, "purchases": data_arr})

@login_required(login_url="/login/")
def purchaseGet(request, id):
   form = ConfirmationForm()
   order = Purchase.objects.get(id=id)
   msg=''

   if not order:
      msg = "order not found"
   
   data_dict = {
         "id": order.id,
         "delivery_date": order.delivery_date,
         "delivery_cost": order.delivery_cost,
         "total_cost": order.total_cost,
         "total_product_cost": order.total_product_cost,
         "payment_method": order.payment_method,
         "remarks": order.remarks,
         "other_cost": order.other_cost,
         "actual_arrival_date":order.actual_arrival_date,
         "status":order.status,
         "purchaseitems": []
      }

   for purchase_item in order.purchase_items.all():
         data_dict['purchaseitems'].append({
            "product_id":purchase_item.product.product_id,
            "product_chinese_name":purchase_item.product.product_chinese_name,
            "product_english_name":purchase_item.product.product_english_name,
            "supplier_product_name":purchase_item.product.supplier_product_name,
            "supplier_name":purchase_item.product.supplier.company_name if purchase_item.product.supplier else "",
            "supplier_code":purchase_item.product.supplier.supplier_id if purchase_item.product.supplier else "",
            "raw_material_cost":purchase_item.raw_material_cost, 
            "packaging_cost":purchase_item.packaging_cost,
            "packaging_cost":purchase_item.packaging_cost,
            "product_other_cost":purchase_item.product_other_cost,
            "freight_cost":purchase_item.freight_cost,
            "sub_total":purchase_item.total_cost,
            "purchase_quantity":purchase_item.recommended_purchase_quantity,
            "delivered_quantity":purchase_item.delivered_quantity,
            "damage_quantity":purchase_item.damage_quantity
            })
   return render(request, 'home/purchase-deatils.html', {"form": form, "order":data_dict, "msg":msg})


@login_required(login_url="/login/")
def purchaseCreate(request):

   products = Inventory.objects.all()
   for product in products:
        product.recommended_purchase_quantity = product.safety_quantity - product.current_quantity
   msg = ''
   form = PurchaseForm()
   if request.method == "POST":

      form = PurchaseForm(request.POST)
      if form.is_valid():
         order_details = request.POST.get('productDetails', None)
         order_details = json.loads(order_details)
         try:
            with transaction.atomic():
               purchase_items = []
               for order in order_details:
                  product = PurchaseItems.objects.create(**order)
                  product.save()
                  purchase_items.append(product)
                  
               if not form.cleaned_data['delivery_date']:
                  delivery_date = datetime.now() + timedelta(days=7)
               else:
                  delivery_date = form.cleaned_data['delivery_date']

               purchase = Purchase.objects.create(
                  delivery_date=delivery_date,
                  delivery_cost=form.cleaned_data['delivery_cost'],
                  total_cost=form.cleaned_data['total_cost'],
                  total_product_cost=form.cleaned_data['total_product_cost'],
                  payment_method=form.cleaned_data['payment_method'],
                  other_cost=form.cleaned_data['other_cost'],
                  type="Purchase")

               purchase.purchase_items.add(*purchase_items)
               purchase.purchase_id="QT" + str('{:07d}'.format(purchase.id))
               purchase.save()

               product = Inventory.objects.filter(product_id=order["product_id"])
               product = product.first()
               product.total_purchased_quantity = order.get('recommended_purchase_quantity')
               product.last_purchase_date = datetime.now().date()
               
               product.save()

               return redirect("purchase-list")
         except Exception as e:
            raise e
   else:
      return render(request, 'home/purchase.html', {"form": form, "products": products})


@login_required(login_url="/login/")
def confirmDelivery(request, id):
   msg=''
   order = Purchase.objects.get(id=id)
   form = ConfirmationForm()

   if not order:
      msg = "order not found"
      return render(request, 'home/purchaseconfirmation.html', {"form": form, "msg":msg})
   
   form = ConfirmationForm(initial={
      'actual_arrival_date':order.actual_arrival_date,
      'status':order.status
   })

   data_dict = {
         "id": order.id,
         "delivery_date": order.delivery_date,
         "delivery_cost": order.delivery_cost,
         "total_cost": order.total_cost,
         "total_product_cost": order.total_product_cost,
         "payment_method": order.payment_method,
         "remarks": order.remarks,
         "other_cost": order.other_cost,
         "status":order.status,
         "actual_arrival_date":order.actual_arrival_date,
         "purchaseitems": []
      }

   for purchase_item in order.purchase_items.all():
         data_dict['purchaseitems'].append({
            "product_id":purchase_item.product.product_id,
            "product_chinese_name":purchase_item.product.product_chinese_name,
            "product_english_name":purchase_item.product.product_english_name,
            "supplier_product_name":purchase_item.product.supplier_product_name,
            "supplier_name":purchase_item.product.supplier.name,
            "supplier_code":purchase_item.product.supplier.code,
            "raw_material_cost":purchase_item.raw_material_cost, 
            "packaging_cost":purchase_item.packaging_cost,
            "packaging_cost":purchase_item.packaging_cost,
            "product_other_cost":purchase_item.product_other_cost,
            "freight_cost":purchase_item.freight_cost,
            "sub_total":purchase_item.total_cost,
            "purchase_quantity":purchase_item.recommended_purchase_quantity,
            "delivered_quantity":purchase_item.delivered_quantity,
            "damage_quantity":purchase_item.damage_quantity,
            })
         
   if request.method == "POST":
      form = ConfirmationForm(request.POST, instance=order)
      
         # Exclude the 'actual_arrival_date' field from form validation
      form.save()
      del form.fields['actual_arrival_date']
      del form.fields['status']

      # Retrieve delivered and damage quantities from POST data
      quantities = json.loads(request.POST.get('quantity', '{}'))
      

      try:
            with transaction.atomic():
               # products = order.purchase_items.filter(product__product_no=quantity['product_id'])
               for quantity in quantities:
                  purchases = order.purchase_items.filter(product__product_no=quantity.get('product_id', ''))
                  purchase = purchases.first()
                  if quantity['delivered_quantity']!='':
                     purchase.delivered_quantity = quantity['delivered_quantity']
                  else:
                     purchase.delivered_quantity = 0
                     quantity['delivered_quantity'] = 0

                  if quantity['damage_quantity']!='':
                     purchase.damage_quntity = quantity['damage_quantity']
                  else:
                     purchase.damage_quntity = 0
                     quantity['damage_quantity'] = 0

                  purchase.save()
                  
                  product = Inventory.objects.filter(product__product_no=quantity.get('product_id', ''))
                  product = product.first()
                  product.total_purchased_quantity = product.total_purchased_quantity - (int(quantity['delivered_quantity'])+int(quantity['damage_quantity']))
                  product.total_stock_in_quantity = int(quantity['delivered_quantity'])
                  product.save()

            msg = _("Purchase information updated successfully")

            return redirect(f"purchase-get", id=id)
      except Exception as e:
            msg = f"Error updating purchase information: {str(e)}"

   return render(request, 'home/purchaseconfirmation.html', {"form": form, "order": data_dict, "msg": msg})


@login_required(login_url="/login/")
def PurchaseDelete(request, id):
   msg = ""
   form = PurchaseForm()
   
   purchase = Purchase.objects.filter(id=id)
   ordertype = purchase.first().type
   purchase.first().purchase_items.all().delete() #deletes the related records
   purchase.delete()
   
   msg = _(f"{ordertype} deleted successfully")
      
   if ordertype=="Quotation": 
      return redirect("quotation-list")
   elif ordertype=="Purchase":
      return redirect("purchase-list")