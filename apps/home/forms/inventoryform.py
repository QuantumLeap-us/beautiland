from django import forms
from apps.home.models import Inventory, Product
class InvetoryForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(),widget=forms.Select, required=False)
    current_quantity = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder":"Actual Quantity",
        "class":"form-control"
    }))
    safety_quantity = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder":"Safety Quantity",
        "class":"form-control"
    }))

    class Meta:
        model = Inventory
        fields = ('product', "safety_quantity",)