from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control

from tipout_demo.models import OtherFunds, EnterOtherFundsForm, DemoEmployee, Balance, Savings
from tipout_demo.budget_with_balance import update_budgets, weekly_budget_simple

from custom_auth.models import TipoutUser

from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def enter_other_funds(request):
	u = TipoutUser.objects.get(email=request.user)
	emp = DemoEmployee.objects.get(user=u)
	emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

	if request.method == 'POST':
		form = EnterOtherFundsForm(request.POST)
		if form.is_valid():
			other_funds_data = form.cleaned_data

			new_other_funds = OtherFunds.objects.create(owner=emp,
														amount=other_funds_data['amount'],
														date_earned=other_funds_data['date_earned'],
														note=other_funds_data['note']
			)

			# only query savings if savings_percent > 0
			if emp.savings_percent > 0:
			    # not sure if this should count as a savings 'deposit'
			    emp_savings = Savings.objects.get(owner=emp)
			    emp_savings.amount += new_other_funds.amount * (emp.savings_percent/100)
			    emp_savings.save()

			    cache.set(emp_cache_key+'savings', emp_savings)

			# update balance
			# if savings_percent == 0, then balance is increased by amount of new_other_funds
			balance = Balance.objects.get(owner=emp)
			balance.amount += new_other_funds.amount * (1 - (emp.savings_percent/100))
			balance.save()

			# update cached balance
			cache.set(emp_cache_key+'balance', balance)

			# update cached other funds
			other_funds = OtherFunds.objects.filter(owner=emp)
			cache.set(emp_cache_key+'other_funds', other_funds)

			current_budget = update_budgets(emp, now().date())
			wk_budget = weekly_budget_simple(emp)
			cache.set(emp_cache_key+'current_budget', current_budget)
			cache.set(emp_cache_key+'weekly_budget', wk_budget)

			return redirect('/demo/other-funds/')

	else:
		form = EnterOtherFundsForm()
		return render(request, 'demo-enter_other_funds.html', {'form': form})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def other_funds(request):
	u = TipoutUser.objects.get(email=request.user)
	emp = DemoEmployee.objects.get(user=u)
	emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

	other_funds = cache.get(emp_cache_key+'other_funds')
	if not other_funds:
		other_funds = OtherFunds.objects.filter(owner=emp)
		cache.set(emp_cache_key+'other_funds', other_funds)

	return render(request, 'demo-other_funds.html', {'other_funds': other_funds})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['POST'])
def delete_other_funds(request, funds_id):
	u = TipoutUser.objects.get(email=request.user)
	emp = DemoEmployee.objects.get(user=u)
	emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

	if request.method == 'POST':
		funds_to_delete = OtherFunds.objects.get(owner=emp, pk=funds_id)

		# save amount, date for updating savings, balance, budget, other funds
		funds_amount = funds_to_delete.amount
		funds_date = funds_to_delete.date_earned

		funds_to_delete.delete()

		# update other funds cache
		other_funds = OtherFunds.objects.filter(owner=emp)
		cache.set(emp_cache_key+'other_funds', other_funds)

		if emp.savings_percent > 0:
			emp_savings = Savings.objects.get(owner=emp)
			emp_savings.amount -= funds_amount * (emp.savings_percent/100)

			# update cache
			cache.set(emp_cache_key+'savings', emp_savings)

		# update balance
		emp_balance = Balance.objects.get(owner=emp)
		emp_balance.amount -= funds_amount
		emp_balance.save()

		# update cached balance
		cache.set(emp_cache_key+'balance', emp_balance)

		# update budget (including cache)
		current_budget = update_budgets(emp, funds_date)
		wk_budget = weekly_budget_simple(emp)
		cache.set(emp_cache_key+'current_budget', current_budget)
		cache.set(emp_cache_key+'weekly_budget', wk_budget)

		return redirect('/demo/other-funds/')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def edit_other_funds(request, funds_id):
	pass
