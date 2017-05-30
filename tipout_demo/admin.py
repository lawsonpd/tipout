from django.contrib import admin

from .models import DemoEmployee, Tip, Expense, Budget

# Register your models here.

class TipAdmin(admin.ModelAdmin):
    fields = ['owner', 'amount', 'date_earned']
    list_display = ('owner', 'amount', 'date_earned')

admin.site.register([DemoEmployee, Expense, Budget])

admin.site.register(Tip, TipAdmin)
