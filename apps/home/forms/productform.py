from django import forms
from apps.home.model.product import Product
from apps.home.model.product_category import Category

from django.utils.translation import gettext_lazy as _

from apps.home.model.supplier import Supplier

BRANDCHOICE = [
    ('MCDerma', 'MCDerma'),
    ('Others', 'Others'),
]

MEASUREMENT_UNIT = [
    ('gram', 'gram'),
    # ('kg', 'kg'),
]
MEASUREMENT_CHOICES = [
    ('bottle', _('bottle')),
    ('Bag', _('Bag')),
    ('box', _('box')),
    ('strip', _('strip')),
    ('piece', _('piece')),
    ('open', _('open')),
    ('etc', _('etc')),
]
STATUS = [
    ('In Sales', _('In Sales')),
    ('In Preparation', _('In Preparation')),
    ('Offlined', _('Offlined')),
]

SALES_CURRENCY_OPTIONS = {
    ('CNY','CNY'),
    ('USD','USD'),
    ('HKD','HKD')
    }

COST_CURRENCY_OPTIONS = {
    ('HKD','HKD'),
    ('RMB','RMB'),
    ('USD','USD'),
}

class ProductForm(forms.ModelForm):

    product_id = forms.CharField(widget=forms.TextInput(
        attrs={
            "placeholder": "Product Number",
            "class": "form-control"
        }
    ), required=False)
    
    product_chinese_name = forms.CharField(widget=forms.TextInput(
        attrs={
            "placeholder": "Product Chinese name",
            "class": "form-control"
        }
    ))
    product_english_name = forms.CharField(widget=forms.TextInput(
        attrs={
            "placeholder": "Product English name",
            "class": "form-control"
        }
    ), required=False)

    product_pic = forms.ImageField(widget=forms.FileInput(attrs={
        "class": "form-control",
        'multiple': True
    }), required=False)

    supplier_product_name = forms.CharField(widget=forms.TextInput(
        attrs={
            "placeholder": "Supplier product name",
            "class": "form-control"
        }
    ), required=False)

    barcode_no = forms.CharField(widget=forms.TextInput(
        attrs={
            "placeholder": "barcode Number",
            "class": "form-control"
        }
    ), required=False)

    category = forms.ModelChoiceField(widget=forms.Select(attrs={
        "class": "form-control"
    }),
        queryset=Category.objects.all(), required=False)
    
    sub_category = forms.ModelChoiceField(widget=forms.Select(attrs={
        "class": "form-control"
    }),
        queryset=Category.objects.all(), required=False)
    
    brand = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control"
    }), choices=BRANDCHOICE)

    unit_of_measurement = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control"
    }), choices=MEASUREMENT_CHOICES)

    unit_weight_category = forms.ChoiceField(
        widget=forms.Select(attrs={
            "class": "form-control"
        }), choices=MEASUREMENT_UNIT)
    
    unit_weight = forms.FloatField(widget=forms.NumberInput(
        attrs={
            "placeholder": "Unit weight",
            "class": "form-control"
        }
    ))

    status = forms.ChoiceField(widget=forms.Select(attrs={
        "class": "form-control"
    }), choices=STATUS)

    sales_currency = forms.ChoiceField(
        widget=forms.Select(attrs={
            "class": "form-control"
        }), choices=SALES_CURRENCY_OPTIONS)
    
    retail_price = forms.FloatField(widget=forms.NumberInput(
        attrs={
            "placeholder": "Retail price",
            "class": "form-control"
        }
    ))

    selling_price = forms.FloatField(widget=forms.NumberInput(
        attrs={
            "placeholder": "Selling price",
            "class": "form-control"
        }
    ))

    std_cost_of_sales = forms.FloatField(widget=forms.NumberInput(
        attrs={
            "placeholder": "Standard cost of Sales",
            "class": "form-control"
        }
    ))

    safety_quantity = forms.IntegerField(widget=forms.TextInput(attrs={
        "placeholder": "Safety Quantity",
        "class": "form-control"
    }))

    # supplier_no = forms.IntegerField(widget=forms.TextInput(attrs={
    #     "placeholder":"Supplier No.",
    #     "class":"form-control"
    # }))

    # supplier_name = forms.CharField(widget=forms.TextInput(attrs={
    #     "placeholder":"Supplier Name",
    #     "class":"form-control"
    # }))

    supplier = forms.ModelChoiceField(widget=forms.Select(attrs={
        "class":"form-control"
    }),queryset=Supplier.objects.exclude(status="draft").all())
    
    shelf_life = forms.DateField(widget=forms.DateInput(attrs={
        "class":"form-control bdc-grey-200 start-date",
        "data-provide":"datepicker",
        "placeholder":"Shelf Life"
    }))
     
    ingredient_list = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder":"Ingredient List",
        "class":"form-control"
    }), required=False)

    # product_info_remarks = forms.CharField(widget=forms.TextInput(attrs={
    #     "placeholder":"Product information Remarks",
    #     "class":"form-control"
    # }), required=False)

    # raw_material_cost = forms.FloatField(widget=forms.TextInput(attrs={
    #     "placeholder":"Raw Material cost",
    #     "class":"form-control"
    # }), required=False)

    # packging_cost=forms.FloatField(widget=forms.TextInput(attrs={
    #     "placeholder":"Packging cost",
    #     "class":"form-control"
    # }), required=False)

    # processing_cost=forms.FloatField(widget=forms.TextInput(attrs={
    #     "placeholder":"Processing cost",
    #     "class":"form-control"
    # }), required=False)

    # other_cost=forms.FloatField(widget=forms.TextInput(attrs={
    #     "placeholder":"Other cost",
    #     "class":"form-control"
    # }), required=False)

    # freight_cost=forms.FloatField(widget=forms.TextInput(attrs={
    #     "placeholder":"freight cost to Hong Kong",
    #     "class":"form-control"
    # }))

    # cost_currency=forms.ChoiceField(widget=forms.Select(attrs={
    #     "class":"form-control"
    # }),choices=COST_CURRENCY_OPTIONS)
    
    # recommended_purchase_quantity = forms.IntegerField(widget=forms.TextInput(attrs={
    #     "placeholder":"Recommended Purchase Quantity",
    #     "class":"form-control"
    # }))
    class Meta:
        model = Product
        fields = ('product_chinese_name', 'product_english_name', 'product_pic' ,'supplier_product_name', 
                  'category', 'sub_category', 'barcode_no', 'brand','unit_of_measurement', 'unit_weight_category', 
                  'unit_weight', 'status', 'sales_currency', 'retail_price', 'selling_price','std_cost_of_sales', 
                  'safety_quantity', 'supplier', 'shelf_life','ingredient_list',
                #   'product_info_remarks', 'raw_material_cost', 'packging_cost', 'processing_cost', 
                #   'other_cost', 'freight_cost', 'cost_currency', 'recommended_purchase_quantity'
                )