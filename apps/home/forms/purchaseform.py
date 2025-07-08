from django import forms
from apps.home.models import Purchase, Product

from django.utils.translation import gettext_lazy as _

PAYMENT_METHOD = {
    ('COD', _('COD')),
    ('Bank Transfer/Cheque', _('Bank Transfer/Cheque')),
}

class PurchaseForm(forms.ModelForm):

    delivery_date = forms.DateField(widget=forms.DateInput(attrs={
        "class": "form-control bdc-grey-200 start-date",
        "data-provide": "datepicker",
        "placeholder": "Delivery Date"
    }), required=False)

    delivery_cost = forms.IntegerField(widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "Delivery Cost"
    }))

    other_cost = forms.IntegerField(widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "Other Cost"
    }))

    total_product_cost = forms.IntegerField(widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": " Total Product Cost"
    }))
    total_cost = forms.IntegerField(widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": " Total Cost"
    }))

    remarks = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder":"Remarks",
        "class":"form-control"
    }), required=False)

    payment_method = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control"
    }), choices=PAYMENT_METHOD)

    class Meta:
        model = Purchase
        fields = ('delivery_date', 'delivery_cost', 'total_product_cost', 'other_cost', 'total_cost', 'payment_method')
