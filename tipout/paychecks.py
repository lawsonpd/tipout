from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from django.utils.timezone import now, timedelta

from tipout.models import (Employee,
                           Paycheck,
                           Balance,
                           Expenditure,
                           EnterPaycheckForm,
                           EditPaycheckForm,
                           Savings,
                           SavingsTransaction
)

from tipout.budget_with_balance import update_budgets, weekly_budget_simple
from custom_auth.models import TipoutUser

from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

# need to be able to view paychecks by month & year
@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def paychecks(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    recent_paychecks = cache.get(emp_cache_key+'recent_paychecks')
    if not recent_paychecks:
        all_paychecks = cache.get(emp_cache_key+'all_paychecks')
        if not all_paychecks:
            all_paychecks = Paycheck.objects.filter(owner=emp)
            cache.set(emp_cache_key+'all_paychecks', all_paychecks)
        recent_paychecks = all_paychecks.filter(date_earned__gt=now().date()-timedelta(30))
        cache.set(emp_cache_key+'recent_paychecks', recent_paychecks)

    return render(request, 'paychecks.html', {'paychecks': recent_paychecks})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def paychecks_archive(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    all_paychecks = cache.get(emp_cache_key+'all_paychecks')
    if not all_paychecks:
        all_paychecks = Paycheck.objects.filter(owner=emp)
        cache.set(emp_cache_key+'all_paychecks', all_paychecks)

    return render(request, 'paychecks_archive.html', {'paychecks': all_paychecks})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def enter_paycheck(request):
    if request.method == 'POST':
        form = EnterPaycheckForm(request.POST)
        if form.is_valid():
            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)
            emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

            paycheck_data = form.cleaned_data

            all_paychecks = cache.get(emp_cache_key+'all_paychecks')
            if not all_paychecks:
                all_paychecks = Paycheck.objects.filter(owner=emp)
                cache.set(emp_cache_key+'all_paychecks', all_paychecks)

            dupe = all_paychecks.filter(date_earned=paycheck_data['date_earned'])
            if dupe:
                return render(request,
                              'enter_paycheck.html',
                              {'error_message': 'Paycheck from that date exists.',
                               'form': EnterPaycheckForm()})
            else:
                p = Paycheck(owner=emp,
                             amount=paycheck_data['amount'],
                             date_earned=paycheck_data['date_earned'],
                             hours_worked=paycheck_data['hours_worked'],
                            )
                p.save()

                # update savings
                if emp.savings_percent > 0:
                    # not sure if this should count as a savings 'deposit'
                    # s = SavingsTransaction.objects.create(owner=emp,
                    #                                       date=p.amount,
                    #                                       amount=p.amount * (emp.savings_percent/100)
                    # )
                    emp_savings = Savings.objects.get(owner=emp)
                    emp_savings.amount += p.amount * (emp.savings_percent/100)
                    emp_savings.save()
                    # update savings cache
                    cache.set(emp_cache_key+'savings', emp_savings)

                # update balance
                # if savings percent == 0, then balance is increased by paycheck amount
                balance = Balance.objects.get(owner=emp)
                balance.amount += p.amount * (1 - (emp.savings_percent/100))
                balance.save()

                # update balance cache
                cache.set(emp_cache_key+'balance', balance)

                # update paycheck cache
                all_paychecks = Paycheck.objects.filter(owner=emp)
                cache.set(emp_cache_key+'all_paychecks', all_paychecks)
                recent_paychecks = all_paychecks.filter(date_earned__gt=now().date()-timedelta(30))
                cache.set(emp_cache_key+'recent_paychecks', recent_paychecks)

                if p.date_earned > now().date()-timedelta(30):
                    recent_paychecks = all_paychecks.filter(date_earned__gt=now().date()-timedelta(30))
                    cache.set(emp_cache_key+'recent_paychecks', recent_paychecks)

                # update_budgets return today's budget amount
                budget_today = update_budgets(emp, p.date_earned)

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

                return redirect('/paychecks/')
    else:
        return render(request,
                      'enter_paycheck.html',
                      {'form': EnterPaycheckForm()}
                     )

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def edit_paycheck(request, p, *args):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    # split paycheck url into (email, 'paycheck', year, month, day)
    # paycheck_data_split = args[0].split('-')

    all_paychecks = cache.get(emp_cache_key+'all_paychecks')
    if not all_paychecks:
        all_paychecks = Paycheck.objects.filter(owner=emp)
        cache.set(emp_cache_key+'all_paychecks', all_paychecks)

    paycheck = all_paychecks.get(pk=p)

    if request.method == 'POST':
        form = EditPaycheckForm(request.POST)
        if form.is_valid():
            paycheck_data = form.cleaned_data

            # update savings
            # do this before updating paycheck so we can compare amounts
            if emp.savings_percent > 0 and paycheck_data['amount'] != paycheck.amount:
                emp_savings = Savings.objects.get(owner=emp)
                emp_savings.amount += ((paycheck_data['amount'] - paycheck.amount) * (emp.savings_percent/100))
                emp_savings.save()

                cache.set(emp_cache_key+'savings', emp_savings)

                # update balance
                balance = Balance.objects.get(owner=emp)
                balance.amount += (paycheck_data['amount'] - paycheck.amount) * (1 - emp.savings_percent/100)
                balance.save()

            elif emp.savings_percent == 0 and paycheck_data['amount'] != paycheck.amount:
                # update balance for when savings percent == 0
                balance = Balance.objects.get(owner=emp)
                balance.amount += paycheck_data['amount'] - paycheck.amount
                balance.save()

            # update balance cache
            cache.set(emp_cache_key+'balance', balance)

            paycheck.amount = paycheck_data['amount']
            paycheck.hours_worked = paycheck_data['hours_worked']
            paycheck.date_earned = paycheck_data['date_earned']
            paycheck.save()

            # update paycheck cache
            all_paychecks = Paycheck.objects.filter(owner=emp)
            cache.set(emp_cache_key+'all_paychecks', all_paychecks)
            recent_paychecks = all_paychecks.filter(date_earned__gt=now().date()-timedelta(30))
            cache.set(emp_cache_key+'recent_paychecks', recent_paychecks)

            # update_budgets return today's budget amount
            budget_today = update_budgets(emp, paycheck.date_earned)

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

            return redirect('/paychecks/')

    else:
        form = EditPaycheckForm(initial={'amount': paycheck.amount,
                                         'hours_worked': paycheck.hours_worked,
                                         'date_earned': paycheck.date_earned
                                        }
                               )
        return render(request, 'edit_paycheck.html', {'form': form, 'paycheck': paycheck})


# May not ever need to delete a paycheck
@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['POST'])
def delete_paycheck(request, p):
    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)
        emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

        all_paychecks = cache.get(emp_cache_key+'all_paychecks')
        if not all_paychecks:
            all_paychecks = Paycheck.objects.filter(owner=emp)
            cache.set(emp_cache_key+'all_paychecks', all_paychecks)

        paycheck_to_delete = all_paychecks.get(pk=p)
        # for exp in es:
        #     if strip(exp.get_absolute_url(), '/') == args[0]:
        #         e = exp

        # need date for budgets update
        paycheck_date = paycheck_to_delete.date_earned

        # update savings
        # do this before deleting the paycheck so we can get the amount
        if emp.savings_percent > 0:
            emp_savings = Savings.objects.get(owner=emp)
            emp_savings.amount -= (paycheck_to_delete.amount * (emp.savings_percent/100))
            emp_savings.save()

            cache.set(emp_cache_key+'savings', emp_savings)

            # update balance
            balance = Balance.objects.get(owner=emp)
            balance.amount -= paycheck_to_delete.amount * (1 - emp.savings_percent/100)
            balance.save()

        else:
            # update balance for when savings percent == 0
            balance = Balance.objects.get(owner=emp)
            balance.amount -= paycheck_to_delete.amount
            balance.save()

        # update balance cache
        cache.set(emp_cache_key+'balance', balance)

        paycheck_to_delete.delete()

        # update paycheck cache
        all_paychecks = Paycheck.objects.filter(owner=emp)
        cache.set(emp_cache_key+'all_paychecks', all_paychecks)
        recent_paychecks = all_paychecks.filter(date_earned__gt=now().date()-timedelta(30))
        cache.set(emp_cache_key+'recent_paychecks', recent_paychecks)

        # update_budgets return today's budget amount
        budget_today = update_budgets(emp, paycheck_date)

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

        return redirect('/paychecks/')

