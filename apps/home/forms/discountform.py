from django import forms

from apps.home.model.discount import DiscountScheme, Coupon, Promotion, PromoCode


class DiscountSchemeForm(forms.ModelForm):
    class Meta:
        model = DiscountScheme
        fields = ['name', 'type', 'condition_amount', 'start_date', 'end_date', 'usage_limit', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'type', 'discount_value', 'min_spend', 'start_date', 'end_date', 'usage_limit']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['name', 'type', 'start_date', 'end_date', 'description']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        fields = ['code', 'discount_value', 'start_date', 'end_date', 'usage_limit']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }