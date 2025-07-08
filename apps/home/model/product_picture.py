from django.db import models
from apps.home.models import Commons, Product

from django.utils.translation import gettext_lazy as _


def product_image_path(instance, filename):
    return f'media/product_images/{instance.id}/{filename}'

class ProductPicture(Commons):
    id=models.BigAutoField(primary_key=True)
    image_name=models.CharField(max_length=128,null=False)
    image=models.ImageField(upload_to=product_image_path)
    product=models.ForeignKey(Product, null=False, on_delete=models.CASCADE)

    class Meta:
        db_table='product_picture'
        verbose_name = _('product picture')
        verbose_name_plural = _('product pictures')

    def __str__(self) -> str:
        return self.image_name
    
    def save(self,*args,**kwargs):

        if self.image:
            self.image_name = self.image.name
            super(ProductPicture,self).save(*args,**kwargs)