from tipout_demo.models import Savings, SavingsTransaction, Balance, DemoEmployee, SavingsSetupForm, SavingsTransactionForm
from budget_with_balance import weekly_budget_simple

from custom_auth.models import TipoutUser

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control

from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

#
# Don't update budgets in savings views, since savings isn't accounted for in budgets
#

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def savings(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    savings = cache.get(emp_cache_key+'savings')
    if not savings:
        savings = Savings.objects.get(owner=emp)
        cache.set(emp_cache_key+'savings', savings)

    return render(request, 'savings.html', {'savings_amount': savings.amount})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def savings_setup(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    if request.method == 'POST':
    	form = SavingsSetupForm(request.POST)
        if form.is_valid():

            savings_data = form.cleaned_data

            # make sure percent > 0

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
            emp = DemoEmployee.objects.get(user=u)
            emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

            trans_data = form.cleaned_data
            if request.POST['inlineRadioOptions'] == 'withdraw':
                amt = trans_data['amount'] * -1
            elif request.POST['inlineRadioOptions'] == 'deposit':
                amt = trans_data['amount']

            t = SavingsTransaction.objects.create(owner=emp,
                                                  date=trans_data['date'],
                                                  amount = amt
            )

            savings = Savings.objects.get(owner=emp)
            savings.amount += amt
            savings.save()

            cache.set(emp_cache_key+'savings', savings)

            balance = Balance.objects.get(owner=emp)
            balance.amount -= amt
            balance.save()

            cache.set(emp_cache_key+'balance', balance)

            # update_budgets return today's budget amount
            budget_today = update_budgets(emp, now().date())

            # update cached budget
            today_expends = cache.get(emp_cache_key+'today_expends')
            if not today_expends:
                today_expends = Expenditure.objects.filter(owner=emp, date=now().date())
                cache.set(emp_cache_key+'today_expends', today_expends)

            expends_sum = sum([exp.cost for exp in today_expends])
            current_budget = budget_today - expends_sum
            cache.set(emp_cache_key+'current_budget', current_budget)

            wk_budget = weekly_budget_simple(emp)
            cache.set(emp_cache_key+'weekly_budget', wk_budget)

            return redirect('/savings/')

    else:
        form = SavingsTransactionForm()
        return render(request, 'savings_transaction.html', {'form': form})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def savings_transaction_history(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    savings_trans = cache.get(emp_cache_key+'savings_trans')
    if not savings_trans:
        savings_trans = SavingsTransaction.objects.filter(owner=emp).order_by('-date')
        cache.set(emp_cache_key+'savings_trans', savings_trans)

    return render(request, 'savings_transaction_history.html', {'trans': savings_trans})
