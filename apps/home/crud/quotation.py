from datetime import datetime, timedelta
import json

from django.http import HttpResponse
from apps.home.forms.purchaseform import PurchaseForm

from apps.home.models import PurchaseItems, Purchase,Inventory

import pdfkit
from django.utils.decorators import method_decorator 
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string


@login_required(login_url="/login/")
def quotationList(request):
    order = Purchase.objects.filter(type="Quotation")
    data_arr = []

    for product in order:
        data_dict = {
            "id": product.id,
            "purchase_id": product.purchase_id,
            "purchaseitems": []
        }

        for purchase_item in product.purchase_items.all():
            data_dict['purchaseitems'].append({
                "product_id":purchase_item.product.product_id,
                "product_chinese_name":purchase_item.product.product_chinese_name,
                "product_english_name":purchase_item.product.product_english_name,
                "supplier_product_name":purchase_item.product.supplier_product_name,
                "sub_total":purchase_item.total_cost,
                "purchase_quantity":purchase_item.recommended_purchase_quantity,
                "supplier_name":purchase_item.product.supplier.name,
                "supplier_code":purchase_item.product.supplier.code,
                })
            
        data_arr.append(data_dict)
    return render(request, 'home/quotation-list.html', {"purchases": data_arr})

@login_required(login_url="/login/")
def quotationGet(request, id):
   order = Purchase.objects.get(id=id)
   msg=''

   if not order:
      msg = "quotation not found"
   
   data_dict = {
         "id": order.id,
         "purchaseitems": []
      }

   for purchase_item in order.purchase_items.all():
         data_dict['purchaseitems'].append({
            "purchase_id":purchase_item.id,
            "product_id":purchase_item.product.product_id,
            "product_chinese_name":purchase_item.product.product_chinese_name,
            "product_english_name":purchase_item.product.product_english_name,
            "supplier_product_name":purchase_item.product.supplier_product_name,
            "purchase_quantity":purchase_item.recommended_purchase_quantity,
            "supplier_name":purchase_item.product.supplier.name,
            "supplier_code":purchase_item.product.supplier.code,
            })
   return render(request, 'home/quotation-deatils.html', {"order":data_dict, "msg":msg})

@login_required(login_url="/login/")
def quotationCreate(request):
    # products = Inventory.objects.all()
    products = Inventory.objects.filter(current_quantity__lt=F('safety_quantity'))

    for product in products:
        product.recommended_purchase_quantity = product.safety_quantity - product.current_quantity 
    
    if request.method=="POST":
        order_details = request.POST.get('productDetails', None)
        order_details = json.loads(order_details)
        purchase_items = []
        with transaction.atomic():
            for order in order_details:
                product = PurchaseItems.objects.create(**order)
                product.save()
                purchase_items.append(product)

            purchase = Purchase.objects.create()
            purchase.purchase_items.add(*purchase_items)
            purchase.purchase_id="QT" + str('{:07d}'.format(purchase.id))
            purchase.type="Quotation"
            purchase.save()
            
            messages.success(request, "Quotation added successfully!")
            return redirect("quotation-get", purchase.id)

    return render(request, 'home/quotation.html', {"products": products})

@method_decorator(csrf_exempt, name='dispatch')
def quotationUpdate(request, id):
    
    order = Purchase.objects.get(id=id)
    msg=''

    if not order:
        msg = "quotation not found"
    
    data_dict = {
            "id": order.id,
            "purchaseitems": []
        }

    for purchase_item in order.purchase_items.all():
            data_dict['purchaseitems'].append({
                "purchase_id":purchase_item.id,
                "product_id":purchase_item.product.product_id,
                "product_chinese_name":purchase_item.product.product_chinese_name,
                "product_english_name":purchase_item.product.product_english_name,
                "supplier_product_name":purchase_item.product.supplier_product_name,
                "purchase_quantity":purchase_item.recommended_purchase_quantity,
                "supplier_name":purchase_item.product.supplier.name,
                "supplier_code":purchase_item.product.supplier.code,
                })
            
    if request.method=="POST":
        order_details=request.POST.get('orderDetails', None)
        order_details = json.loads(order_details)
        with transaction.atomic():
            for obj in order_details:
                item = PurchaseItems.objects.filter(id=obj['id'])
            
                if item:
                    item.update(recommended_purchase_quantity=obj['recommended_purchase_quantity']) 
                    
            messages.success(request, "Quotation updated successfully.")
            return redirect("quotation-get", order.id)
        
    return render(request, 'home/quotation-update.html', {"order":data_dict, "msg":msg})


@login_required(login_url="/login/")
def quotationPdf(request, id):
    order = Purchase.objects.get(id=id)
    msg=''

    if not order:
        msg = "quotation not found"
    
    data_dict = {
            "id": order.purchase_id,
            "purchaseitems": []
        }

    for purchase_item in order.purchase_items.all():
            data_dict['purchaseitems'].append({
                "purchase_id":purchase_item.id,
                "product_id":purchase_item.product.product_id,
                "product_chinese_name":purchase_item.product.product_chinese_name,
                "product_english_name":purchase_item.product.product_english_name,
                "supplier_product_name":purchase_item.product.supplier_product_name,
                "purchase_quantity":purchase_item.recommended_purchase_quantity,
                "supplier_name":purchase_item.product.supplier.name,
                "supplier_code":purchase_item.product.supplier.code,
                })
            
    # return render(request,'home/quotation-template.html', {"order":data_dict})
    template = render_to_string('home/quotation-template.html', {"order":data_dict})

    default_options = {
        "enable-local-file-access": True,
        "page-size": "A4",  # Adjust the page size as needed
        "encoding": "utf-8"
    }
    pdf = pdfkit.from_string(template,  options=default_options)
    
    output_path=f"media/{order.purchase_id}.pdf"
    with open(output_path, 'wb') as pdf_file:
            pdf_file.write(pdf)

    with open(output_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={order.purchase_id}.pdf'
            return response
        

@login_required(login_url="/login/")
def quotationToPurchase(request, id):
    order = Purchase.objects.get(id=id)
    form = PurchaseForm()
    msg=''

    if not order:
        msg = "quotation not found"
    
    data_dict = {
            "id": order.purchase_id,
            "purchaseitems": []
        }

    for purchase_item in order.purchase_items.all():
            data_dict['purchaseitems'].append({
                "id":purchase_item.product.id,
                "product_id":purchase_item.product.product_id,
                "product_chinese_name":purchase_item.product.product_chinese_name,
                "product_english_name":purchase_item.product.product_english_name,
                "supplier_product_name":purchase_item.product.supplier_product_name,
                "purchase_quantity":purchase_item.recommended_purchase_quantity,
                "supplier_name":purchase_item.product.supplier.name,
                "supplier_code":purchase_item.product.supplier.code,
                })
            
    if request.method == "POST":

      form = PurchaseForm(request.POST)
      if form.is_valid():
         order_details = request.POST.get('productDetails', None)
         order_details = json.loads(order_details)
         try:
            with transaction.atomic():
               purchase_items = []
               for orderdict in order_details:
                  product = PurchaseItems.objects.filter(product_id=orderdict['id']).update(
                      recommended_purchase_quantity=orderdict['recommended_purchase_quantity'],
                      raw_material_cost = orderdict['raw_material_cost'],
                      packaging_cost=orderdict['packaging_cost'],
                      processing_cost=orderdict['processing_cost'],
                      product_other_cost=orderdict['product_other_cost'],
                      freight_cost=orderdict['freight_cost'],
                      total_cost=orderdict['total_cost'])
                  purchase_items.append(product)

               if not form.cleaned_data['delivery_date']:
                  delivery_date = datetime.now() + timedelta(days=7)
               else:
                  delivery_date = form.cleaned_data['delivery_date']

               purchase = Purchase.objects.filter(id=id)
               purchase.update(
                  delivery_date=delivery_date,
                  delivery_cost=form.cleaned_data['delivery_cost'],
                  total_cost=form.cleaned_data['total_cost'],
                  total_product_cost=form.cleaned_data['total_product_cost'],
                  payment_method=form.cleaned_data['payment_method'],
                  other_cost=form.cleaned_data['other_cost'],
                  remarks=form.cleaned_data['remarks'],
                  type="Purchase")

               product = Inventory.objects.filter(product_id=orderdict["id"])
               product = product.first()
               product.total_purchased_quantity = orderdict.get('recommended_purchase_quantity')
               product.last_purchase_date = datetime.now().date()
               product.save()

               return redirect("purchase-list")
         except Exception as e:
            raise e
        
    return render(request,'home/quotationtopurchase.html', {"order":data_dict, "form":form})
    
