from apps.home.model.product_category import Category
from apps.home.models import Commons
from django.db import models
from django.core.validators import RegexValidator

from apps.authentication.models import User

from django.utils.translation import gettext_lazy as _
import os


INDUSTRY_CATEGORY = {
('beauty salon','beauty salon'),
('massage parlor','massage parlor'),
('manicure store','manicure store'),
('retail store','retail store'),
('street guest','street guest'),
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

STATUS_CHOICES = [
        ("draft", "Draft"),
        ("potential customer", "Potential Customer"),
        ("converted customer", 'Converted Customer'),
        ("paid customer", 'Paid Customer'),
        ("inactive customer", 'Inactive Customer'),
    ]

def get_file_path(instance, filename):
    # Upload path: user/<user_id>/image.jpg
    return f"media/customer/{instance.customer.id}/{filename}"


class Customer(Commons):
    id = models.BigAutoField(primary_key=True)
    customer_id = models.CharField(max_length=500, null=True, blank=True, unique=True)
    industry_type = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    english_name = models.CharField(max_length=128, null=True, blank=True)
    company_name = models.CharField(max_length=128)
    company_english_name = models.CharField(max_length=128)
    contact_person_1 = models.CharField(max_length=128)
    contact_person_1_chinese = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=128, validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    contact_person_2 = models.CharField(max_length=128, null=True, blank=True)
    contact_person_2_chinese = models.CharField(max_length=128, null=True, blank=True)
    phone_number_2 = models.CharField(max_length=128, null=True, blank=True, validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    landline = models.CharField(max_length=128, null=True, blank=True, validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    accumlated_sales = models.CharField(max_length=500, null=True, blank=True, validators=[
        RegexValidator(
            r'^[0-9]*$', 'Only Numbers are allowed.')])
    country = models.CharField(max_length=128)
    district_in_hk = models.CharField(max_length=128)
    prefix = models.CharField(max_length=128)
    currency = models.CharField(max_length=250)
    email = models.EmailField(null=True, blank=True)
    source = models.CharField(max_length=128)
    sale_person = models.ForeignKey(User, related_name='customers', null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=128, choices=STATUS_CHOICES)
    delivery_comments = models.TextField(null=True, blank=True)
    customer_comments = models.TextField(null=True, blank=True)
    created_by=models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        db_table = 'customer'
        verbose_name = _('customer')
        verbose_name_plural = _('customers')

    def __str__(self) -> str:
        return self.company_name

class Address(Commons):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128)
    address_line = models.CharField(max_length=500, verbose_name="Main address")
    address_line_chinese = models.CharField(max_length=500, verbose_name="Main address in chinese")
    address_2 = models.CharField(max_length=500, null=True, blank=True)
    address_2_chinese = models.CharField(max_length=500, null=True, blank=True)
    address_3 = models.CharField(max_length=500, null=True, blank=True)
    address_3_chinese = models.CharField(max_length=500, null=True, blank=True)
    customer = models.ForeignKey(Customer, related_name='addresses', on_delete=models.CASCADE)

    
    class Meta:
        db_table = 'address'
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        
    def __str__(self) -> str:
        return f"{self.customer.name} - {self.name}"


class Customer_Files(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_file_path, blank=True, null=True)
    file_name = models.CharField(max_length=500, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Retrieve old file path before saving the new file
        old_file = None
        if self.pk:
            old_file = Customer_Files.objects.get(pk=self.pk).file

        # Call the superclass' save() method
        super().save(*args, **kwargs)

        # Delete the old file if it exists
        if old_file:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)
