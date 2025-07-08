# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from apps.authentication.models import *
# Register your models here.

admin.site.register(User)
admin.site.register(ProfilePic)
admin.site.register(Permissions)