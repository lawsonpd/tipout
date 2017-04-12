from __future__ import unicode_literals
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.encoding import python_2_unicode_compatible
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

@python_2_unicode_compatible
class Employee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employees')
    new_user = models.BooleanField()
    init_avg_daily_tips = models.FloatField()
    signup_date = models.DateField(default=date.today)

    def __str__(self):
        return self.user.username

# @python_2_unicode_compatible
class Tip(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tips')
    # should amount be FloatField?
    amount = models.FloatField()
    # DEFAULT_HOURS_WORKED = 8
    hours_worked = models.FloatField(default=8.0)
    date_earned = models.DateField(default=date.today)

    def __str__(self):
        return str(self.date_earned) + ' ' + str(self.amount)

class Paycheck(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paychecks')
    # should amount be FloatField?
    amount = models.FloatField()
    # need to represent overtime somehow (?)
    hours_worked = models.FloatField(default=80.0)
    date_earned = models.DateField(default=date.today)
    # frequency = models.CharField(default='BW')

    def get_absolute_url(self):
        return '%s-paycheck-%s' % (self.owner.username, slugify(self.date_earned))

class Expense(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    expense_name = models.CharField(max_length=100)
    cost = models.FloatField()
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
    def get_absolute_url(self):
        expense_name_split = expense_name.split(' ')
        url_name = '-'.join(expense_name_split)
        return "/%s" % url_name

class Expenditure(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenditures')
    cost = models.FloatField()
    note = models.CharField(max_length=100, default="expenditure")
    date = models.DateField(default=date.today)

    def __str__(self):
        return self.owner.username + ' ' +  self.note + ' ' + str(self.date)

    def get_absolute_url(self):
        return "/%s-%s-%s/" % (self.owner.username, self.note, slugify(self.date))

    def month_name(self):
        return self.date.strftime("%B")

# not sure if Budget is needed. can we get the data insights we want
# just by having the Tip and Expense models?
class Budget(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budget')
    daily_budget = models.FloatField()

class EnterTipsForm(ModelForm):
    class Meta:
        model = Tip
        exclude = ['owner', 'hours_worked']

class EditTipForm(ModelForm):
    class Meta:
        model = Tip
        exclude = ['owner', 'hours_worked', 'date_earned']

class EnterPaycheckForm(ModelForm):
    class Meta:
        model = Paycheck
        # assume default hrs worked (80) for now
        exclude = ['owner', 'hours_worked']

class EditPaycheckForm(ModelForm):
    class Meta:
        model = Paycheck
        exclude = ['owner', 'hours_worked', 'date_earned']

class EnterExpenseForm(ModelForm):
    class Meta:
        model = Expense
        exclude = ['owner']

class EditExpenseForm(ModelForm):
    class Meta:
        model = Expense
        exclude = ['owner', 'expense_name', 'frequency']

class EnterExpenditureForm(ModelForm):
    class Meta:
        model = Expenditure
        exclude = ['owner']

class NewUserSetupForm(ModelForm):
    class Meta:
        model = Employee
        exclude = ['user', 'new_user', 'signup_date']
        labels = {
            'init_avg_daily_tips': _('Estimated daily tips'),
        }

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields
