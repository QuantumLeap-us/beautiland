from django import forms
from apps.home.model.product_category import Category
from apps.home.models import Customer
from django.core.validators import RegexValidator

from django.utils.translation import gettext_lazy as _

INDUSTRY_CATEGORY = {
('beauty salon',_('beauty salon')),
('massage parlor',_('massage parlor')),
('manicure store',_('manicure store')),
('retail store',_('retail store')),
('street guest',_('street guest')),
}

AREA_CODES = {('+52', '+52 (Mexico)'), 
              ('+33', '+33 (France)'), 
              ('+7', '+7 (Russia)'), 
              ('+49', '+49 (Germany)'), 
              ('+65', '+65 (Singapore)'), 
              ('+64', '+64 (New Zealand)'), 
              ('+1', '+1 (Canada)'), 
              ('+1', '+1 (US)'), 
              ('+20', '+20 (Egypt)'), 
              ('+34', '+34 (Spain)'), 
              ('+44','+44 (UK)'), 
              ('+81', '+81 (Japan)'), 
              ('+61', '+61 (Australia)'), 
              ('+971', '+971 (UAE)'), 
              ('+82', '+82 (South Korea)'), 
              ('+966', '+966 (Saudi Arabia)'), 
              ('+55', '+55 (Brazil)'), 
              ('+39', '+39 (Italy)'), 
              ('+86', '+86 (China)'), 
              ('+91', '+91 (India)')}


class CustomerForm(forms.ModelForm):
    
    name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Name",
        "class": "form-control inputField"
    }))
    
    english_name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "English Name",
        "class": "form-control inputField"
    }))

    company_name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Company Name",
        "class": "form-control inputField"
    }))
    company_english_name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Company English Name",
        "class": "form-control inputField"
    }))

    industry_category = forms.ModelChoiceField(widget=forms.Select(
        attrs={
            "class":"form-control inputField"
        }    
    ), queryset=Category.objects.filter(type="Industry Category"))

    contact_1 = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Contact 1",
        "class": "form-control inputField"
    }), validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])

    contact_2 = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Contact 2",
        "class": "form-control inputField"
    }), validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    
    area_code = forms.ChoiceField(widget=forms.Select(attrs={
        "class":"form-control inputField"
    }),choices=AREA_CODES)

    phone_number = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Phone Number",
        "class": "form-control inputField"
    }), validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])

    phone_number_2 = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Phone Number 2",
        "class": "form-control inputField"
    }), validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])

    # fax_number = forms.IntegerField(widget=forms.TextInput(attrs={
    #     "placeholder": "Fax Number",
    #     "class": "form-control"
    # }), validators=[
    #     RegexValidator(
    #         r'^[0-9]*$', 'Only Numbers are allowed.')])

    email = forms.EmailField(widget=forms.TextInput(attrs={
        "placeholder": "Email",
        "class": "form-control inputField"
    }))

    url = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "URL",
        "class": "form-control inputField"
    }))

    landline = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Landline",
        "class": "form-control inputField"
    }), validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    
    customer_comments = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Customer Comments",
        "class": "form-control inputField"
    }), required=False)
    delivery_comments = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Delivery Comments",
        "class": "form-control inputField"
    }), required=False)
    class Meta:
        model = Customer
        fields = ('name', 'english_name', 'company_name', 'company_english_name', 'industry_category', 'contact_1', 'contact_2', 'area_code', 
                  'phone_number', 'phone_number_2', 'email', 'url', 'landline', 'customer_comments', 'delivery_comments')
        
class CustomerSmallForm(forms.ModelForm):
    
    name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Name",
        "class": "form-control inputField"
    }))

    company_name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Company Name",
        "class": "form-control inputField"
    }))

    customer_comments = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Customer Comments",
        "class": "form-control inputField"
    }), required=False)

    delivery_comments = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Delivery Comments",
        "class": "form-control inputField"
    }), required=False)

    phone_number = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Phone Number",
        "class": "form-control inputField"
    }), validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])

    class Meta:
        model = Customer
        fields = ('name', 'company_name', 'phone_number', 'customer_comments', 'delivery_comments')