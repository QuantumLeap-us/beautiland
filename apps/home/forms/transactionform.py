from django import forms
from apps.home.model.transaction import Transaction

class TransactionForm(forms.ModelForm):
    attachment = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control-file', 'accept': '.pdf,.jpg,.jpeg,.png'}))

    class Meta:
        model = Transaction
        fields = [
            'transaction_type', 'amount', 'currency', 'payment_method', 'status',
            'payment_status', 'refund_amount', 'refund_date', 'delivery_date', 'remarks', 'attachment'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(choices=[('HKD', 'HKD'), ('USD', 'USD'), ('CNY', 'CNY')], attrs={'class': 'form-control'}),
            'payment_method': forms.Select(choices=[
                ('', 'Select Payment Method'),
                ('Cash', 'Cash'),
                ('Cheque', 'Cheque'),
                ('Bank Transfer', 'Bank Transfer'),
                ('COD', 'COD'),
            ], attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'refund_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'refund_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'delivery_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("金额必须大于0")
        return amount

    def clean_refund_amount(self):
        refund_amount = self.cleaned_data.get('refund_amount')
        if refund_amount < 0:
            raise forms.ValidationError("退款金额不能为负")
        return refund_amount

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if not attachment.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise forms.ValidationError("Only PDF or image files (.jpg, .jpeg, .png) are allowed.")
        return attachment