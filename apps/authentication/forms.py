# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from apps.authentication.models import User
from datetime import datetime

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))


ROLES=[
    ('admin','admin'),
    ('staff','staff'),
    ('seller','seller')
]


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Email",
                "class": "form-control"
            }
        ))
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "re-type password",
                "class": "form-control"
            }
        ))
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "First name",
                "class": "form-control"
            }
        ))
    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last name",
                "class": "form-control"
            }
        ))
    mobile = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Mobile",
                "class": "form-control"
            }
        ))
    role = forms.ChoiceField(widget=forms.Select, choices=ROLES)
    birthdate = forms.DateField(widget=forms.SelectDateWidget(empty_label="Nothing", years=range(1950,datetime.now().year+1)))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2','first_name', 'last_name', 'mobile', 'role', 'birthdate')
