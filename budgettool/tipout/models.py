from __future__ import unicode_literals
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible
from django.forms import ModelForm

@python_2_unicode_compatible
class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employees')
    new_user = models.BooleanField()
    init_avg_daily_tips = models.IntegerField()
    signup_date = models.DateField(default=date.today)
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50)
#
    def __str__(self):
        return self.user.username

# @python_2_unicode_compatible
class Tip(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tips')
    amount = models.IntegerField()
    # DEFAULT_HOURS_WORKED = 8
    hours_worked = models.FloatField(default=8)
    date_earned = models.DateField(default=date.today)

    # def __str__(self):
    #     return str(self.amount)

class Expense(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    expense_name = models.CharField(max_length=100)
    cost = models.IntegerField()
    DAILY = 'DA'
    BI_WEEKLY = 'BW'
    MONTHLY = 'MO'
    YEARLY = 'YR'
    FREQ_CHOICES = (
        (DAILY, 'Daily'),
        (BI_WEEKLY, 'Bi-weekly'),
        (MONTHLY, 'Monthly'),
        (YEARLY, 'Yearly'),
    )
    frequency = models.CharField(max_length=2,
                                 choices=FREQ_CHOICES,
                                 default=MONTHLY)

class Expenditure(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenditures')
    cost = models.IntegerField()
    note = models.CharField(max_length=100, default="Expenditure")
    date = models.DateField(default=date.today)

# not sure if Budget is needed. can we get the data insights we want
# just by having the Tip and Expense models?
class Budget(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budget')
    daily_budget = models.FloatField()

class EditTipsForm(ModelForm):
    class Meta:
        model = Tip
        exclude = ['owner', 'hours_worked']

class EditExpensesForm(ModelForm):
    class Meta:
        model = Expense
        exclude = ['owner', 'frequency']

class EnterExpenditureForm(ModelForm):
    class Meta:
        model = Expenditure
        exclude = ['owner']
