from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control

from decimal import Decimal

from tipout.models import Tip, Expenditure, EnterTipsForm, Employee, SavingsTransaction, Savings, Balance
from custom_auth.models import TipoutUser
from .budget_utils import (avg_daily_tips_earned,
                          avg_daily_tips_earned_initial,
                          tips_available_per_day_initial,
                          tips_available_per_day,
                          daily_avg_from_paycheck,
                          pretty_dollar_amount
                         )
from .budget_with_balance import update_budgets, weekly_budget_simple
from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def enter_tips(request):
    # if this is a POST request, we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request
        form = EnterTipsForm(request.POST)
        # check whether it's valid
        if form.is_valid():
            tip_data = form.cleaned_data

            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)
            emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

            t = Tip(amount=tip_data['amount'],
                    date_earned=tip_data['date_earned'],
                    owner=emp)
            t.save()

            if emp.savings_percent > 0:
                # not sure if this should count as a savings 'deposit'
                # s = SavingsTransaction.objects.create(owner=emp,
                #                                       date=t.date_earned,
                #                                       amount=t.amount * (emp.savings_percent/100)
                # )
                emp_savings = Savings.objects.get(owner=emp)
                emp_savings.amount += t.amount * (emp.savings_percent/100)
                emp_savings.save()

                cache.set(emp_cache_key+'savings', emp_savings)

            # update balance
            # if savings percent == 0, then balance is increased by t.amount
            balance = Balance.objects.get(owner=emp)
            balance.amount += t.amount * (1 - (emp.savings_percent/100))
            balance.save()

            # update balance cache
            cache.set(emp_cache_key+'balance', balance)

            tips = Tip.objects.filter(owner=emp)
            cache.set(emp_cache_key+'tips', tips)

            # update_budgets return today's budget amount
            budget_today = update_budgets(emp, t.date_earned)

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

            return redirect('/tips/')

    # if a GET (or any other method), we'll create a blank form
    else:
        form = EnterTipsForm()
        return render(request, 'enter_tips.html', {'form': form})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def tips(request):
    '''
    To template:
    ALL tips that belong to current user.
    Daily avg. tips based on ALL user's tips.
    '''
    if request.method == 'GET':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)
        emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

        t = now().date()

        tips = cache.get(emp_cache_key+'tips')
        if not tips:
            tips = Tip.objects.filter(owner=emp)
            cache.set(emp_cache_key+'tips', tips)

        # tips = Tip.objects.filter(owner=emp,
        #                           date_earned__month=now().date().month).order_by('date_earned')[::-1]
        if (t - emp.signup_date).days <= 30:
            tip_values = [ tip.amount for tip in tips ]
            avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date))
            return render(request, 'tips.html', {'avg_daily_tips': avg_daily_tips,
                                                 'avg_based_on_init_avg': True,
                                                 'tips': tips,
                                                 'month': t.strftime('%B')
                                                }
            )
        else:
            recent_tips = tips.filter(date_earned__gt=(t-timedelta(30)))
            tip_values = [ tip.amount for tip in recent_tips ]
            avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned(tip_values))
            return render(request, 'tips.html', {'avg_daily_tips': avg_daily_tips,
                                                 'tips': tips,
                                                 'month': t.strftime('%B')
                                                }
            )

@cache_control(private=True)
@login_required(login_url='/login/')
def edit_tip(request, *args):
    pass

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['POST'])
def delete_tip(request, tip_id, *args):

    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)
        emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

        tips = cache.get(emp_cache_key+'tips')
        if not tips:
            tips = Tip.objects.filter(owner=emp)
            cache.set(emp_cache_key+'tips', tips)

        t = tips.get(owner=emp, pk=tip_id)
        tip_date = t.date_earned

        # update savings
        if emp.savings_percent > 0:
            emp_savings = Savings.objects.get(owner=emp)
            emp_savings.amount -= (t.amount * (emp.savings_percent/100))
            emp_savings.save()

            cache.set(emp_cache_key+'savings', emp_savings)

            # update balance
            balance = Balance.objects.get(owner=emp)
            balance.amount -= t.amount * (1 - (emp.savings_percent/100))
            balance.save()

        # update balance
        balance = Balance.objects.get(owner=emp)
        balance.amount -= t.amount
        balance.save()

        # update balance cache
        cache.set(emp_cache_key+'balance', balance)

        t.delete()

        tips = Tip.objects.filter(owner=emp)
        cache.set(emp_cache_key+'tips', tips)

        # update_budgets return today's budget amount
        budget_today = update_budgets(emp, tip_date)

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

        return redirect('/tips/')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def tips_archive(request, year=None, month=None, day=None, *args):
    '''
    See past tips.

    Render the same template but send different data depending on the
    parameters that are past in.
    '''

    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    tips = cache.get(emp_cache_key+'tips')
    if not tips:
        tips = Tip.objects.filter(owner=emp)
        cache.set(emp_cache_key+'tips', tips)

    if not year:
        all_years = [tip.date_earned.year for tip in tips]
        years = set(all_years)
        return render(request, 'tips_archive.html', {'years': years})

    elif not month:
        dates = tips.filter(date_earned__year=year).dates('date_earned', 'month')
        months = [date.month for date in dates]
        return render(request, 'tips_archive.html', {'year': year,
                                                     'months': months})
    elif not day:
        dates = tips.filter(date_earned__year=year,
                            date_earned__month=month).dates('date_earned', 'day')
        days = [date.day for date in dates]
        return render(request, 'tips_archive.html', {'year': year,
                                                     'month': month,
                                                     'days': days})
    else:
        tips_for_day = tips.filter(date_earned__year=year,
                                   date_earned__month=month,
                                   date_earned__day=day)
        return render(request, 'tips_archive.html', {'year': year,
                                                     'month': month,
                                                     'day': day,
                                                     'tips': tips_for_day})
