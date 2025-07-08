import json
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.home.forms.voucherform import VoucherForm
from apps.home.models import Product, Category, Voucher, ProductCombo, DiscountVoucher

@login_required(login_url="/login/")
def voucherList(request):
    form = VoucherForm()
    vouchers = Voucher.objects.all()

    return render(request, 'home/voucher-list.html', {"vouchers": vouchers, 'form': form})
    
@login_required(login_url="/login/")
def voucherGet(request, id):
    msg = ''
    only_available_to = None
    discount_voucher = None
    form = VoucherForm()
    voucher = Voucher.objects.get(id=id)
    # product_combo = ProductCombo.objects.get(id=voucher.product_combo.id)
    # discount_voucher = DiscountVoucher.objects.select_related('only_available_to').get(id=voucher.discount_voucher.id)
    if voucher.discount_voucher:
        discount_voucher = DiscountVoucher.objects.get(id=voucher.discount_voucher.id)
        only_available_to = discount_voucher.only_available_to.all()

    if not voucher:
        msg = _("product not found")

    return render(request, 'home/voucher-details.html', {"voucher": voucher, 'discount_voucher':discount_voucher, "only_available_to":only_available_to,'form': form, 'msg':msg})

@login_required(login_url="/login/")
def addVoucher(request):
    msg=''
    form = VoucherForm()
    products = Product.objects.all()
    categories = Category.objects.all()

    if request.method == "POST":
        form = VoucherForm(request.POST)

        if form.is_valid():
                
            with transaction.atomic():
                    if form.cleaned_data['voucher_type'] == "Product Combo":
                        
                        combos = request.POST.get('productDetails', None)
                        combos = json.loads(combos)

                        for combo in combos:
                            discount_type = combo.pop('discount_type')
                            discount_value = combo.pop('discount_value')
                            combo.pop("id")

                            combo_obj = ProductCombo.objects.create(**combo)
                            
                            voucher = Voucher.objects.create(chinese_name=form.cleaned_data['chinese_name'],
                                                            english_name=form.cleaned_data['english_name'],
                                                            voucher_highlights=form.cleaned_data['voucher_highlights'],
                                                            voucher_details=form.cleaned_data['voucher_details'],
                                                            voucher_type=form.cleaned_data['voucher_type'],
                                                            discount_type=discount_type,
                                                            discount_value=discount_value,
                                                            quota=form.cleaned_data['quota'],
                                                            start_date=form.cleaned_data['start_date'],
                                                            end_date=form.cleaned_data['end_date'],
                                                            status=form.cleaned_data['status'],
                                                            product_combo=combo_obj,
                                                            created_by=request.user
                                                            )
                            voucher.voucherid = ("".join([word[0][0]for word in form.cleaned_data['voucher_type'].split(" ")]) + 
                                        "".join([word[0][0] for word in discount_type.split(" ")])) + str('{:07d}'.format(voucher.id))
                            voucher.save()
                            msg=_('voucher sucessfully added!')
                        return redirect("voucher-list")
                            
                    elif form.cleaned_data['voucher_type']=="Discount Voucher" or form.cleaned_data['voucher_type']=="Free Gift":
                        products=request.POST.get('productDetails', None)
                        products=json.loads(products)
                        products[0].pop("id")
                        discount_type = products[0].pop('discount_type')
                        discount_value = products[0].pop('discount_value')
                        only_available_to = products[0].pop("only_available_to")

                        discount_voucher = DiscountVoucher.objects.create(**products[0])
                        discount_voucher.only_available_to.add(*only_available_to)
                        discount_voucher.save()

                        voucher = Voucher.objects.create(chinese_name=form.cleaned_data['chinese_name'],
                                                        english_name=form.cleaned_data['english_name'],
                                                        voucher_highlights=form.cleaned_data['voucher_highlights'],
                                                        voucher_details=form.cleaned_data['voucher_details'],
                                                        voucher_type=form.cleaned_data['voucher_type'],
                                                        discount_type=discount_type,
                                                        discount_value=discount_value if discount_value else None,
                                                        quota=form.cleaned_data['quota'],
                                                        start_date=form.cleaned_data['start_date'],
                                                        end_date=form.cleaned_data['end_date'],
                                                        status=form.cleaned_data['status'],
                                                        discount_voucher=discount_voucher,
                                                        created_by=request.user
                                                        )
                        voucher.voucherid = ("".join([word[0][0]for word in form.cleaned_data['voucher_type'].split(" ")]) + 
                                    "".join([word[0][0] for word in discount_type.split(" ")])) + str('{:07d}'.format(voucher.id))
                        voucher.save()
                        msg=_('voucher sucessfully added!')
                        return redirect("voucher-list")
        else:
            msg=form.errors


    return render(request, 'home/voucher.html', {"form":form, 'products':products, 'categories':categories, 'msg':msg})

@login_required(login_url="/login/")
def voucherDelete(request, id):
    msg = ""
    form = VoucherForm()
    try:
        Voucher.objects.filter(id=id).delete()
        msg = _("Voucher deleted successfully")
    except Exception as e:
        raise e
    vouchers = Voucher.objects.all()
    return render(request, 'home/voucher-list.html', {"msg": msg, "vouchers": vouchers, 'form': form})