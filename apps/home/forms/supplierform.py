from django import forms
from apps.home.models import Supplier
from django.core.validators import RegexValidator

from django.utils.translation import gettext_lazy as _

class SupplierForm(forms.ModelForm):

    name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Name",
        "class": "form-control"
    }))

    english_name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "English Name",
        "class": "form-control"
    }))

    code = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Supplier Code",
        "class": "form-control"
    }))

    phone_number = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Phone Number",
        "class": "form-control"
    }), validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])

    email = forms.EmailField(widget=forms.TextInput(attrs={
        "placeholder": "Email",
        "class": "form-control"
    }))

    address_line1 = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Address line 1",
        "class": "form-control"
    }))

    address_line2 = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Address line 2",
        "class": "form-control"
    }),required=False)

    pincode = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Pincode",
        "class": "form-control"
    }), validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    
    landmark = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Landmark",
        "class": "form-control"
    }),required=False)

    town = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Town",
        "class": "form-control"
    }))

    city = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "City",
        "class": "form-control"
    }))

    state = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "State",
        "class": "form-control"
    }))
    
    country = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Country",
        "class": "form-control"
    }))

    class Meta:
        model = Supplier
        fields = ('name', 'english_name', 'code', 'phone_number', 'email', 
                  'address_line1', 'address_line2', 'pincode', 'landmark', 
                  'town', 'city', 'state', 'country',)
