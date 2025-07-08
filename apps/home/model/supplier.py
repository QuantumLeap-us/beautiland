
from apps.home.model.commons import Commons
from django.db import models
from django.core.validators import RegexValidator
from apps.home.forms.customerform import AREA_CODES
from apps.authentication.models import User
import os


def get_file_path(instance, filename):
    # Upload path: user/<user_id>/image.jpg
    return f"media/supplier/{instance.supplier.id}/{filename}"

class Supplier(Commons):
    id = models.BigAutoField(primary_key=True)
    supplier_id=models.CharField(max_length=50, unique=True)
    supplier_type=models.CharField(max_length=100)
    product_type=models.CharField(max_length=100)
    company_name=models.CharField(max_length=250)
    location=models.CharField(max_length=250)
    currency=models.CharField(max_length=250)
    prefix=models.CharField(max_length=250, choices=AREA_CODES)
    contact_type=models.CharField(max_length=250)
    contact_person_1=models.CharField(max_length=128)
    phone_1=models.CharField(max_length=128, null=True, blank=True, validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    contact_person_2=models.CharField(max_length=128, null=True, blank=True)
    phone_2=models.CharField(max_length=128, null=True, blank=True, validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    email = models.EmailField(null=True, blank=True)
    website=models.CharField(max_length=500, null=True, blank=True)
    remark=models.CharField(max_length=500, null=True, blank=True)
    purchasing_comments=models.TextField(null=True, blank=True)
    status=models.CharField(max_length=100, null=True, blank=True)
    last_po_date=models.DateTimeField(null=True, blank=True)
    created_by=models.ForeignKey(User, on_delete=models.PROTECT)

    # code = models.CharField(max_length=128)
    # name = models.CharField(max_length=128)
    # english_name = models.CharField(max_length=128, null=True)
    # phone_number = models.CharField(max_length=128, validators=[
    #     RegexValidator(
    #         r'^[0-9]*$', 'Only Numbers are allowed.')])
    # address_line1 = models.CharField(max_length=128, null=True)
    # address_line2 = models.CharField(max_length=128, null=True)
    # pincode = models.PositiveIntegerField()
    # landmark = models.CharField(max_length=128, null=True)
    # town = models.CharField(max_length=128)
    # city = models.CharField(max_length=128)
    # state = models.CharField(max_length=128)
    # country = models.CharField(max_length=128)

    class Meta:
        db_table='supplier'

    def __str__(self)->str:
        return f"{self.supplier_id} - {self.company_name}"
        # return f"{self.code} - {self.name} - {self.english_name}"

class Supplier_Files(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_file_path, blank=True, null=True)
    file_name = models.CharField(max_length=500, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Retrieve old file path before saving the new file
        old_file = None
        if self.pk:
            old_file = Supplier_Files.objects.get(pk=self.pk).file

        # Call the superclass' save() method
        super().save(*args, **kwargs)

        # Delete the old file if it exists
        if old_file:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)
