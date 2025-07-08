from django import forms
from django.core.validators import RegexValidator

from apps.home.model.customer import Address

class AddressForm(forms.ModelForm):
    address_line = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Address line ",
        "class": "form-control"
    }))
    # address_line2 = forms.CharField(widget=forms.TextInput(attrs={
    #     "placeholder": "Address line 2",
    #     "class": "form-control"
    # }),required=False)
    # pincode = forms.IntegerField(widget=forms.TextInput(attrs={
    #     "placeholder": "Pincode",
    #     "class": "form-control"
    # }), validators=[
    #     RegexValidator(
    #         r'^[0-9]*$', 'Only Numbers are allowed.')])
    # landmark = forms.CharField(widget=forms.TextInput(attrs={
    #     "placeholder": "Landmark",
    #     "class": "form-control"
    # }),required=False)
    # town = forms.CharField(widget=forms.TextInput(attrs={
    #     "placeholder": "Town",
    #     "class": "form-control"
    # }))
    # city = forms.CharField(widget=forms.TextInput(attrs={
    #     "placeholder": "City",
    #     "class": "form-control"
    # }))
    # state = forms.CharField(widget=forms.TextInput(attrs={
    #     "placeholder": "State",
    #     "class": "form-control"
    # }))
    # country = forms.CharField(widget=forms.TextInput(attrs={
    #     "placeholder": "Country",
    #     "class": "form-control"
    # }))
    
    class Meta:
        model = Address
        fields = ['address_line']