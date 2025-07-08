# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from apps.home.models import Commons
from django.core.validators import RegexValidator
# Create your models here.

class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, username, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=username,**extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role','admin')

        if extra_fields.get('is_active') is not True:
            raise ValueError(_('Superuser must have is_active=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(username, email, password, **extra_fields)


ROLES={
    ('admin',_('admin')),
    ('staff',_('staff')),
    ('seller',_('seller'))
}

def user_profile_pic(instance, file, filename):
    return f"profile_pic/{instance.id}"



class User(AbstractUser, Commons):
    id=models.BigAutoField(primary_key=True)
    role=models.CharField(max_length=128, choices=ROLES, default='seller')
    mobile=models.CharField(max_length=128, null=True, validators=[
        RegexValidator(
            r'^[0-9]*$', _('Only Numbers are allowed.'))])
    birthdate=models.DateField(null=True)

    objects=UserManager()

    class Meta:
        db_table='user'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self) -> str:
        return self.username

class ProfilePic(Commons):
    id=models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=128,null=False)
    image=models.ImageField(upload_to=user_profile_pic, null=False)
    product=models.ForeignKey(User,related_name='profile_pics',null=False,on_delete=models.CASCADE)

    class Meta:
        db_table='profile_pic'
        verbose_name = _('profile pic')
        verbose_name_plural = _('profile pics')

    def __str__(self)->str:
        return self.name
    
class Permissions(models.Model):
    role = models.CharField(max_length=100, choices=ROLES, default='seller')
    permission = models.CharField(max_length=150)
    is_permission = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)