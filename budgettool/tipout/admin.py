from django.contrib import admin

from .models import Tip, Expense, Budget

# Register your models here.

admin.site.register([Tip, Expense, Budget])
