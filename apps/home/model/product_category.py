from django.db import models
from apps.home.models import Commons

from django.utils.translation import gettext_lazy as _ 

class Category(Commons):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128, null=False, blank=False)
    parent = models.ForeignKey("self", related_name="subcategories", null=True, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, null=True)

    class Meta:
        db_table='category'
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self)->str:
        if self.type:
            return f"{self.name} ({self.type})"
        else:
            return self.name
                                                