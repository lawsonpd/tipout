from django.contrib import admin

from .models import Employee, Tip, Expense, Budget

# Register your models here.

admin.site.register([Employee, Tip, Expense, Budget])
