from django import forms
from datetime import date

class SignupForm(forms.Form):
    pass

class EnterTipsForm(forms.Form):
    tips_amount = forms.IntegerField(label="tips amount", min_value=0, max_value=5000)
    date_earned = forms.DateField(label="date earned (use form 'yyyy-mm-dd')", initial=date.today())

# class EnterExpensesForm(forms.Form):
#     cost = forms.IntegerField(label="expense amount", min_value=0, max_value=5000)
#     expense_name = forms.CharField(label="expense name", max_length=100)
#     frequency = forms.CharField(label="frequency", initial="MONTHLY")

# class ViewExpensesForm(forms.Form):
#     cost = None

# class EditTipsForm(forms.Form):
#     amount = forms.IntegerField(label="tips amount", min_value=0, max_value=5000)
#     date_earned = forms.DateField(label="date earned (use form 'yyyy-mm-dd')")
#
# class EditExpensesForm(forms.Form):
#     expense_name = forms.CharField(label="expense name", max_length=100)
#     cost = forms.IntegerField(label="expense amount", min_value=0, max_value=5000)
#
# class EnterExpenditureForm(forms.Form):
#     cost = forms.IntegerField(label="expenditure cost", min_value=0, max_value=5000)
#     date = forms.DateField(label="date", initial=date.today())
