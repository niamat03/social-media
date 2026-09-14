from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Profile', {'fields': ('display_name', 'bio', 'avatar')}),
    )
    list_display = ('username', 'email', 'display_name', 'is_staff')
