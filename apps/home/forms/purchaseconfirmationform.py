from django import forms
from apps.home.models import Purchase

from django.utils.translation import gettext_lazy as _

DELIVEREY_STATUS={
    ('Pending', _('Pending')),
    ('Delivered', _('Delivered')),
    ('Partially Delivered', _('Partially Delivered')),
}
class ConfirmationForm(forms.ModelForm):

    actual_arrival_date = forms.DateField(widget=forms.DateInput(attrs={
        "class": "form-control bdc-grey-200 start-date",
        "data-provide": "datepicker",
        "placeholder": "Actual Delivery Date"
    }))

    status = forms.CharField(widget=forms.Select(attrs={
        "class": "form-control",
    },choices=DELIVEREY_STATUS))

    class Meta:
        model = Purchase
        fields = ('actual_arrival_date', 'status')
