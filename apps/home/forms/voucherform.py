from django import forms
from django.utils.translation import gettext_lazy as _

from apps.home.models import Voucher


STATUS = {
    ('Ready to start', _('Ready to start')),
    ('Valid', _('Valid')),
    ('Paused', _('Paused')),
    ('Ended', _('Ended')),
    ('Cancelled', _('Cancelled'))
}

VOUCHER_TYPE = {
    (None,'-------'),
    ('Product Combo', _('Product Combo')),
    ('Discount Voucher', _('Discount Voucher')),
    ('Free Gift', _('Free Gift')),
    ('Manual Discount', _('Manual Discount')),
}

DISCOUNT_TYPE = {
    (None,'-------'),
    ('Fixed Amount', _('Fixed Amount')),
    ('Rate(%)', _('Rate(%)')),
}

TRIGGER_TYPE = {
    (None, '-------'),
    ('More than', _('More than')),
    ('More than and equals to', _('More than and equals to')),
    ('Equals to', _('Equals to')),
    ('Less than and equals to', _('Less than and equals to')),
    ('Less than', _('Less than')),

}


class VoucherForm(forms.ModelForm):
    chinese_name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control"
    }))
    english_name = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control"
    }))
    voucher_details = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control"
    }), required=False)
    voucher_highlights = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control"
    }), required=False)
    voucher_type = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control"
    }), choices=VOUCHER_TYPE)
    # discount_type = forms.ChoiceField(widget=forms.Select(attrs={
    #     "class": "form-control"
    # }), choices=DISCOUNT_TYPE, required=False)
    # discount_value = forms.FloatField(widget=forms.TextInput(attrs={
    #     "class": "form-control"
    # }), required=False)
    quota = forms.IntegerField(widget=forms.NumberInput(attrs={
        "class": "form-control"
    }), required=False)
    start_date = forms.DateField(widget=forms.TextInput(attrs={
        "class": "form-control bdc-grey-200 start-date",
        "data-provide": "datepicker",
    }))
    end_date = forms.DateField(widget=forms.TextInput(attrs={
        "class": "form-control bdc-grey-200 start-date",
        "data-provide": "datepicker",
    }), required=False)
    status = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control"
    }), choices=STATUS)

    class Meta:
        model = Voucher
        fields = ['chinese_name', 'english_name', 'voucher_details', 'voucher_highlights', 'voucher_type', 
                  'quota', 'start_date', 'end_date', 'status']
