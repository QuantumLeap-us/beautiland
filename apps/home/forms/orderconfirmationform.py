from django import forms
from apps.home.models import Order

from django.utils.translation import gettext_lazy as _

DELIVEREY_STATUS={
    ('Pending', _('Pending')),
    ('Received', _('Received')),
}
class OrderConfirmationForm(forms.ModelForm):

    delivery_date = forms.DateField(widget=forms.DateInput(attrs={
        "class": "form-control bdc-grey-200 start-date",
        "data-provide": "datepicker",
        "placeholder": "Delivery Date"
    }))

    status = forms.CharField(widget=forms.Select(attrs={
        "class": "form-control",
    },choices=DELIVEREY_STATUS))

    class Meta:
        model = Order
        fields = ('delivery_date', 'status')
