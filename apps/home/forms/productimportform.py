from django import forms

class importForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={
        "class": "form-control",
        'multiple': True
    }), required=False, )