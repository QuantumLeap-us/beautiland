from django import forms
from apps.home.models import Category

TYPE_OPTIONS = {
('Industry Category','Industry Category'),
('Product Category','Product Category'),
('Supplier Category','Supplier Category'),
}

class CategoryForm(forms.ModelForm):

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder":"name",
                "class":"form-control"
            }
        ), required=True
    )

    parent_id = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={
            "class":"form-control"
        }), required=False)
    
    type = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                "placeholder":"Type",
                "class":"form-control"
            }, 
        ),
        choices=TYPE_OPTIONS, required=True
    )
    
    class Meta:
        model = Category
        fields = ("name", "parent_id", "type")