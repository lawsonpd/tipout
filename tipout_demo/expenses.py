from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from django.utils.timezone import now

from tipout_demo.models import DemoEmployee, Expense, Balance, Expenditure, EnterExpenseForm, EditExpenseForm, PayExpenseForm
from budget_with_balance import update_budgets, weekly_budget_simple
from custom_auth.models import TipoutUser

from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenses(request):
    '''
    Get expenses that belong to current user and pass them to the template.
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expenses = cache.get(emp_cache_key+'expenses')
    if not expenses:
        expenses = Expense.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expenses', expenses)

    return render(request, 'demo-expenses.html', {'expenses': expenses})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def enter_expense(request):
    '''
    On POST request, get expenses data from form and update db.
    On GET request, show enter_expenses template/form.
    '''
    if request.method == 'POST':
        form = EnterExpenseForm(request.POST)
        if form.is_valid():
            u = TipoutUser.objects.get(email=request.user)
            emp = DemoEmployee.objects.get(user=u)

            expense_data = form.cleaned_data

            emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

            expenses = cache.get(emp_cache_key+'expenses')
            if not expenses:
                expenses = Expense.objects.filter(owner=emp)
                cache.set(emp_cache_key+'expenses', expenses)

            if expenses.filter(expense_name=expense_data['expense_name']).exists():
                return render(request,
                              'demo-enter_expense.html',
                              {'form': EnterExpenseForm(),
                               'error_message': 'An expense with that name already exists.'}
                )
            else:
                exp = Expense.objects.create(owner=emp,
                                             cost=expense_data['cost'],
                                             expense_name=expense_data['expense_name'],
                                             frequency=expense_data['frequency']
                )

                expenses = Expense.objects.filter(owner=emp)
                cache.set(emp_cache_key+'expenses', expenses)

                # update_budgets return today's budget amount
                budget_today = update_budgets(emp, exp.date_added)

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

                return redirect('/demo/expenses/')
    else:
        form = EnterExpenseForm()
        return render(request, 'demo-enter_expense.html', {'form': form})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def edit_expense(request, *args):
    exp_name = args[0].replace('-', ' ')

    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expenses = cache.get(emp_cache_key+'expenses')
    if not expenses:
        expenses = Expense.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expenses', expenses)

    exp = expenses.get(expense_name=exp_name)

    if request.method == 'GET':
        form = EditExpenseForm(initial={'cost': exp.cost})
        return render(request, 'demo-edit_expense.html', {'form': form, 'expense': exp})

    if request.method == 'POST':
        form = EditExpenseForm(request.POST)
        if form.is_valid():
            exp_data = form.cleaned_data
            ##
            # Need to check for dupe here
            ##
            # exp = Expense.objects.get(owner=emp, expense_name=e.expense_name)
            exp.cost = exp_data['cost']
            exp.save()

            expenses = Expense.objects.filter(owner=emp)
            cache.set(emp_cache_key+'expenses', expenses)

            # update_budgets return today's budget amount
            budget_today = update_budgets(emp, exp.date_added)

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

            return redirect('/demo/expenses/')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['POST'])
def delete_expense(request, *args):
    exp_name = args[0].replace('-', ' ')

    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = DemoEmployee.objects.get(user=u)

        emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

        expenses = cache.get(emp_cache_key+'expenses')
        if not expenses:
            expenses = Expense.objects.filter(owner=emp)
            cache.set(emp_cache_key+'expenses', expenses)

        exp = expenses.get(expense_name=exp_name)

        # save date for update_budgets
        exp_date = exp.date_added

        exp.delete()

        expenses = Expense.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expenses', expenses)

        # update_budgets return today's budget amount
        budget_today = update_budgets(emp, exp_date)

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
        
        return redirect('/demo/expenses/')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def pay_expense(request, exp=None):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expenses = cache.get(emp_cache_key+'expenses')
    if not expenses:
        expenses = Expense.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expenses', expenses)

    if request.method == 'POST':
        form = PayExpenseForm(request.POST)

        if form.is_valid():
            exp_data = form.cleaned_data

            # update paid-on date for expense
            exp_to_pay = expenses.get(pk=exp)
            exp_to_pay.paid_on = exp_data['paid_on']
            exp_to_pay.save()

            # update cached expenses
            expenses = Expense.objects.filter(owner=emp)
            cache.set(emp_cache_key+'expenses', expenses)

            # update emp's balance
            balance = Balance.objects.get(owner=emp)
            balance.amount -= exp_to_pay.cost
            balance.save()

            # update balance cache
            cache.set(emp_cache_key+'balance', balance)

            # update_budgets return today's budget amount
            budget_today = update_budgets(emp, now().date())

            # update cached budget
            today_expends = cache.get(emp_cache_key+'today_expends')
            if not today_expends:
                today_expends = Expenditure.objects.filter(owner=emp, date=now().date())
                cache.set(emp_cache_key+'today_expends', today_expends)

            # update cached expends for budget cache
            expends_sum = sum([exp.cost for exp in today_expends])
            current_budget = budget_today - expends_sum

            cache.set(emp_cache_key+'current_budget', current_budget)

            wk_budget = weekly_budget_simple(emp)
            cache.set(emp_cache_key+'weekly_budget', wk_budget)

            return redirect('/demo/expenses/')

    else:
        form = PayExpenseForm(initial={'paid_on': now().date()})
        return render(request, 'demo-pay_expense.html', {'form': form, 'expenses': expenses})
