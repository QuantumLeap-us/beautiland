from django import forms
from apps.home.models import Order, Customer, Voucher

from django.utils.translation import gettext_lazy as _

PAYMENT_METHODS={
    (None, "-------"),
    ('COD',_('COD')),
    ('Bank Transfer', _('Bank Transfer')),
    ('Cheque', _('Cheque'))
}

DELIVERY_METHOD = {
    (None, "-------"),
    ("self-pickup", _("Self-Pickup")),
    ("SF Express", _("SF Express")),
    ("salesperson delivery", _("Salesperson Delivery")),
    ("GOGOVAN", _("GOGOVAN"))
}

DELIVERY_STATUS = {
    ('Pending', _('Pending')),
    ('Partially Delievered', _('Partially Delievered')),
    ('Delievered', _('Delievered')),
}

PAYMENT_STATUS = {
    (None, "-------"),
    ('Paid', _('Paid')),
    ('Pending', _('Pending')),
    ('Failed', _('Failed'))
}

ORDER_TYPE={
    ("Invoice", _("Invoice")),
    ("Quotation", _("Quotation")),
}

CURRENCY = {
    ('USD','USD'),
    ('CNY','CNY'),
    ('HKD','HKD')
}
class orderForm(forms.ModelForm):

    delivery_address = forms.CharField(max_length=1024, 
                                       widget=forms.Textarea(attrs={
        "class": "form-control inputField",
        "cols":20,
        "rows":3,
        # "style": "width: auto;",
    }),)

    delivery_date = forms.DateField(widget=forms.DateInput(attrs={
        "class": "form-control bdc-grey-200 start-date inputField",
        "data-provide": "datepicker",
        "placeholder": "Delivery Date",
        "data-provide":"datepicker"
    }), required=False)

    delivery_cost = forms.IntegerField(widget=forms.TextInput(attrs={
        "class": "form-control inputField",
        "placeholder": "Delivery Fee",
    }), required=False)

    other_cost = forms.IntegerField(widget=forms.TextInput(attrs={
        "class": "form-control inputField",
        "placeholder": "Other Fee"
    }), required=False)

    total_cost = forms.FloatField(widget=forms.TextInput(attrs={
        "class": "form-control inputField",
        "placeholder": "Total Price"
    }), required=False)

    manual_cost = forms.FloatField(widget=forms.TextInput(attrs={
        "class": "form-control inputField",
        "placeholder": "Special Discount",
        "onkeypress": "return isValidInput(event)",
        "onpaste": "handleTextPaste(event)",
    }), required=False)

    total_quantity = forms.IntegerField(widget=forms.TextInput(attrs={
        "class": "form-control inputField",
        "placeholder": "Total Quantity"
    }))

    delivery_method = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control inputField",
        "placeholder": "Delivery Method",
        # "style": "width: auto;",
    }), required=False, choices=DELIVERY_METHOD)

    delivery_status = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control inputField",
        "placeholder": "Delivery Status",
        # "style": "width: auto;",
    }), choices=DELIVERY_STATUS, required=False)

    payment_method = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control inputField", 
        # "style": "width: auto;",
    }), choices=PAYMENT_METHODS, required=False)

    payment_status = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control inputField",
        "placeholder": "Payment status"
    }), required=False , choices=PAYMENT_STATUS)

    type = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control inputField",
        "placeholder": "Type",
        # "style": "width: auto;",
    }), choices=ORDER_TYPE, initial='Invoice')

    date = forms.DateTimeField(widget=forms.DateInput(attrs={
        "class": "form-control bdc-grey-200 start-date inputField",
        "data-provide": "datepicker",
        "placeholder": "Order Date",
        "data-provide":"datepicker"
    }))

    payment_record = forms.FileField(widget=forms.FileInput, required=False)

    currency = forms.ChoiceField(widget=forms.Select(attrs={
        "class":"form-control inputField"
    }), choices=CURRENCY, initial='HKD')

    approval_comments = forms.CharField(widget=forms.Textarea(attrs={
        "class":"form-control inputField",
        "cols":20,
        "rows":3
    }), required=False)
    class Meta:
        model = Order
        fields = ('delivery_address', 'total_quantity', 'delivery_method', 'delivery_status', 
                  'payment_status', 'type', 'payment_record', 'delivery_date', 'date','delivery_cost', 
                  'other_cost', 'total_cost', 'payment_method', 'manual_cost', 'currency', 'approval_comments')
