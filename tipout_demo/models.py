from __future__ import unicode_literals
from datetime import date
from django.db import models
# from django.contrib.auth.models import User
from custom_auth.models import TipoutUser
from django.contrib.auth.forms import UserCreationForm
from django.utils.encoding import python_2_unicode_compatible
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.utils.timezone import now

@python_2_unicode_compatible
class DemoEmployee(models.Model):
    user = models.OneToOneField(
        TipoutUser,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    new_user = models.BooleanField(default=True)
    init_avg_daily_tips = models.DecimalField(default=0, max_digits=9, decimal_places=2)
    signup_date = models.DateField(default=now)
    # savings_percent is a percentage (max value 99.9)
    savings_percent = models.DecimalField(default=0, max_digits=3, decimal_places=1)

    def __str__(self):
        email_name = self.user.email.split('@')
        return email_name[0]

@python_2_unicode_compatible
class Tip(models.Model):
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='tips')
    # should amount be FloatField?
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    # DEFAULT_HOURS_WORKED = 8
    hours_worked = models.DecimalField(default=8.0, max_digits=9, decimal_places=2)
    date_earned = models.DateField(default=now)

    def __str__(self):
        return str(self.date_earned) + ' ' + str(self.amount)

class Paycheck(models.Model):
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='paychecks')
    # should amount be FloatField?
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    # need to represent overtime somehow (?)
    hours_worked = models.DecimalField(default=80.0, max_digits=9, decimal_places=2)
    date_earned = models.DateField(default=now)
    # frequency = models.CharField(default='BW')

    def get_absolute_url(self):
        return '/%s-paycheck-%s/' % (str(self.owner), slugify(self.date_earned))

class Balance(models.Model):
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='balance')
    amount = models.DecimalField(max_digits=9, decimal_places=2, default=0)

class OtherFunds(models.Model):
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='otherfunds')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    date_earned = models.DateField(default=now)
    note = models.CharField(max_length=100)

class Expense(models.Model):
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='expenses')
    expense_name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=9, decimal_places=2)
    date_added = models.DateField(auto_now_add=True)
    paid_on = models.DateField(default=now)
    FREQ_CHOICES = (
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('BI_WEEKLY', 'Bi-weekly'),
        ('MONTHLY', 'Monthly'),
        ('ANNUALLY', 'Annually'),
    )
    frequency = models.CharField(max_length=9,
                                 choices=FREQ_CHOICES,
                                 default='MONTHLY'
    )
    def get_absolute_url(self):
        expense_name_split = self.expense_name.split(' ')
        url_name = '-'.join(expense_name_split)
        return "/%s" % url_name

@python_2_unicode_compatible
class Expenditure(models.Model):
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='expenditures')
    cost = models.DecimalField(max_digits=9, decimal_places=2)
    note = models.CharField(max_length=100, default="expenditure")
    date = models.DateField(default=now)

    def __str__(self):
        return str(self.owner) + ' ' +  self.note + ' ' + str(self.date)

    def get_absolute_url(self):
        # note_slugified = self.note.replace(' ', '-')
        return "/%s-%s/" % ('expenditure', self.pk)

    def month_name(self):
        return self.date.strftime("%B")

# not sure if Budget is needed. can we get the data insights we want
# just by having the Tip and Expense models?
class Budget(models.Model):
    '''
    Budget amount is the initial budget for the day (i.e. it doesn't take into account
    expenses or expenditures. The 'running' budget is calculated in the view.)
    '''
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='budget')
    date = models.DateField(default=now)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    # positive over_under means user was *under* budget
    over_under = models.DecimalField(max_digits=9, decimal_places=2, default=0)

class Savings(models.Model):
    '''
    This model holds the actual amount the user has in savings. This way a user can remove 
    arbitrary amounts from savings if they wish.

    Records of "deposits" and "withdrawals" from savings are kept in SavingsTransactions objects.
    '''
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(max_digits=11, decimal_places=2, default=0)

class SavingsTransaction(models.Model):
    '''
    Records of savings "deposits" and "withdrawals".
    '''
    owner = models.ForeignKey(DemoEmployee, on_delete=models.CASCADE, related_name='savingstransactions')
    date = models.DateField(default=now)
    # positive -> deposit, negative -> withdrawal
    amount = models.DecimalField(max_digits=11, decimal_places=2)

class Feedback(models.Model):
    # No foreign key to User since user can submit feedback after canceling sub.
    email = models.EmailField()
    feedback = models.TextField()
    refer_likelihood = models.IntegerField()
    date = models.DateField(default=now)

#########
# FORMS #
#########

class EnterTipsForm(ModelForm):
    class Meta:
        model = Tip
        exclude = ['owner']

class EditTipForm(ModelForm):
    class Meta:
        model = Tip
        exclude = ['owner', 'hours_worked', 'date_earned']

class EnterPaycheckForm(ModelForm):
    class Meta:
        model = Paycheck
        exclude = ['owner']

class EditPaycheckForm(ModelForm):
    class Meta:
        model = Paycheck
        exclude = ['owner']

class EnterExpenseForm(ModelForm):
    class Meta:
        model = Expense
        exclude = ['owner', 'last_paid_on']

class EditExpenseForm(ModelForm):
    class Meta:
        model = Expense
        exclude = ['owner', 'expense_name', 'frequency', 'last_paid_on']

class PayExpenseForm(ModelForm):
    class Meta:
        model = Expense
        exclude = ['owner', 'expense_name', 'frequency', 'cost']

class EnterExpenditureForm(ModelForm):
    class Meta:
        model = Expenditure
        exclude = ['owner']

class EditExpenditureForm(ModelForm):
    class Meta:
        model = Expenditure
        exclude = ['owner']

class NewUserSetupForm(ModelForm):
    class Meta:
        model = DemoEmployee
        exclude = ['user', 'new_user', 'signup_date', 'savings_percent']
        labels = {
            'init_avg_daily_tips': _('Estimated daily tips'),
        }

class SavingsSetupForm(ModelForm):
    class Meta:
        model = DemoEmployee
        exclude = ['user', 'new_user', 'signup_date', 'init_avg_daily_tips']
        labels = {
            'savings_percent': _('Percent of income to save'),
        }

class SavingsTransactionForm(ModelForm):
    class Meta:
        model = SavingsTransaction
        exclude = ['owner']

class EditBalanceForm(ModelForm):
    class Meta:
        model = Balance
        exclude = ['owner']

class EnterOtherFundsForm(ModelForm):
    class Meta:
        model = OtherFunds
        exclude = ['owner']

