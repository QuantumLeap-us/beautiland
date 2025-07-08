from datetime import datetime
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from apps.home.forms.addressform import AddressForm
from apps.home.model.customer import Address, Customer


# @login_required(login_url="/login/")
# def AddressList(request):
#     form = AddressForm()
#     customers = Address.objects.all()

#     return render(request, 'home/customer-list.html', {"customers": customers, 'form': form})

@login_required(login_url="/login/")
def addressCreate(request, id):
    msg=""
    form=AddressForm()
    
    
    if request.method == "POST":
        form = AddressForm(request.POST)

        if form.is_valid():

            try:
                obj = form.save(commit=False)
                obj.customer_id=id
                obj.save()
                messages.success(request,  _("Address added successfully"))
                return redirect('customer-details', id)
            except Exception as e:
                raise e
        else:
            messages.error(request, _( "Form is invalid"))
    else:
        msg = ''
        form= AddressForm()
        


    return render(request, 'home/address.html', {"msg": msg, 'form': form })

@login_required(login_url="/login/")
def addressUpdate(request, id):
    msg = ''
    address = Address.objects.filter(id=id)
    if not address:
        msg = _("customer not found")
    else:
        address = address.first()
        form = AddressForm(instance=address)
        
        if request.method == "POST":
            form = AddressForm(request.POST, instance=address)
            if form.is_valid():
                try:
                    obj = form.save()

                    msg = _("Address updated successfully")
                    return redirect('customer-details', obj.customer.id)
                except Exception as e:
                    raise e
            else:
                msg = _("form is invalid")
    return render(request, 'home/address.html', {"msg": msg, 'form': form})


@login_required(login_url="/login/")
def addressDelete(request, id):
    msg =''
    address = Address.objects.filter(id=id)
    customer=address.first().customer.id
    try:
        
        address.delete()
        msg=_("Address deleted successfully")
        return redirect('customer-deatils',)
    except Exception as e:
        pass
    customer = Customer.objects.get(id=customer)
    addresses = customer.addresses.all()
    return render(request, 'home/customer-detail.html', {"msg": msg, "customer":customer, "addresses":addresses})
