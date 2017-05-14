from tipout.models import Savings, SavingsTransaction, Employee, SavingsSetupForm, SavingsTransactionForm

from custom_auth.models import TipoutUser

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def savings(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    savings, created = Savings.objects.get_or_create(owner=emp,
                                            defaults={'amount': 0})

    return render(request, 'savings.html', {'savings_amount': savings.amount})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def savings_setup(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    if request.method == 'POST':
    	form = SavingsSetupForm(request.POST)
        if form.is_valid():

            savings_data = form.cleaned_data

            emp.savings_percent = savings_data['savings_percent']
            emp.save()

            return redirect('/savings/')

    else:
        emp_savings_percent = emp.savings_percent
        form = SavingsSetupForm()
    	return render(request, 'savings_setup.html', {'form': form,
                                                      'savings_percent': emp_savings_percent})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def savings_transaction(request):
    if request.method == 'POST':
        form = SavingsTransactionForm(request.POST)
        if form.is_valid():
            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)

            trans_data = form.cleaned_data
            if request.POST['inlineRadioOptions'] == 'withdraw':
                amt = trans_data['amount'] * -1
            else:
                amt = trans_data['amount']

            t = SavingsTransaction.objects.create(owner=emp,
                                                  date=trans_data['date'],
                                                  amount = amt
            )

            savings = Savings.objects.get(owner=emp)
            savings.amount += amt
            savings.save()

            return redirect('/savings/')

    else:
        form = SavingsTransactionForm()
        return render(request, 'savings_transaction.html', {'form': form})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def savings_transaction_history(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    trans = SavingsTransaction.objects.filter(owner=emp).order_by('-date')

    return render(request, 'savings_transaction_history.html', {'trans': trans})
