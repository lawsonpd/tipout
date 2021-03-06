from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control

from tipout_demo.models import Tip, Paycheck, DemoEmployee, Expense, Expenditure, Budget, OtherFunds, Balance, EditBalanceForm
from .budget_utils import (today_budget,
                          pretty_dollar_amount,
                          expenditures_sum_for_specific_day,
                          # budget_for_specific_day,
                          # update_budgets,
                          # weekly_budget_simple
)
from .budget_with_balance import (budget_for_specific_day,
                                 update_budgets,
                                 weekly_budget_simple
)
from custom_auth.models import TipoutUser

from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def balance(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    balance = cache.get(emp_cache_key+'balance')
    if not balance:
        balance = Balance.objects.get(owner=emp)
        cache.set(emp_cache_key+'balance', balance)

    return render(request, 'demo-balance.html', {'balance': pretty_dollar_amount(balance.amount)})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def edit_balance(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    balance = cache.get(emp_cache_key+'balance')
    if not balance:
        balance_object = Balance.objects.get(owner=emp)
        cache.set(emp_cache_key+'balance', balance)

    if request.method == 'POST':
        form = EditBalanceForm(request.POST)
        if form.is_valid():
            new_balance = form.cleaned_data

            # update balance
            balance.amount = new_balance['amount']
            balance.save()

            # update cached balance
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

            return redirect('/demo/balance/')

    else:
        form = EditBalanceForm(initial={'amount': balance})
        return render(request, 'demo-edit_balance.html', {'form': form})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def budget(request):
    '''
    Get TipoutUser from request context, then get tips belonging to that user
    and pass the daily average for past 30 days to template.

    Since budget is first view upon login, check to see if user is 'new'.
    If so, and it has been less than 30 days since signup, calculate tips
    based on init_avg_daily_tips. Otherwise, calculate based on actual tips.
    '''

    '''
    If user is new, send to new-user-setup to set init_avg_daily_tips.
    '''

    # get user, employee
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    # if user is new, send to new-user-setup
    if emp.new_user:
        return redirect('/demo/new-user-setup/')

    else:
        # avg_daily_tips = pretty_dollar_amount(emp.init_avg_daily_tips)
        # avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned(tip_values))

        #TODO
        # if there is a budget for today, return it
        # otherwise get yesterday's budget,
        #   calculate the over/under for yesterday,
        #   and then return today's budget
        # if there isn't a budget for yesterday,
        #   find the most recent budget and work up to yesterday
        #   (saving the budgets & over/unders for those days)
        # if there are fewer than 7 budgets, do all of them

        current_budget = cache.get(emp_cache_key+'current_budget')

        if not current_budget:
            try:
                budget = Budget.objects.get(owner=emp, date=now().date())
                # exps will not throw exception since if there are none it will be an empty set
                exps = Expenditure.objects.filter(owner=emp, date=now().date())
                exps_sum = sum([exp.cost for exp in exps])
                current_budget = budget.amount - exps_sum
                cache.set(emp_cache_key+'current_budget', current_budget)

            except:
                try:
                    yesterday_budget = Budget.objects.get(owner=emp, date=now().date()-timedelta(1))
                    yesterday_exps = Expenditure.objects.filter(owner=emp, date=now().date()-timedelta(1))
                    yesterday_budget.over_under = yesterday_budget.amount - sum([exp.cost for exp in yesterday_exps])
                    yesterday_budget.save()

                    budget, created = Budget.objects.update_or_create(owner=emp,
                                                                      date=now().date(),
                                                                      defaults={'amount': budget_for_specific_day(emp, now().date())}
                    )

                    exps = Expenditure.objects.filter(owner=emp, date=now().date())
                    exps_sum = sum([exp.cost for exp in exps])
                    current_budget = budget.amount - exps_sum
                    cache.set(emp_cache_key+'current_budget', current_budget)

                except:
                    most_recent_budget = Budget.objects.filter(owner=emp).order_by('-date')[0]
                    mrb_date = most_recent_budget.date

                    # over/under for most_recent_budget
                    exps = Expenditure.objects.filter(owner=emp, date=mrb_date)
                    most_recent_budget.over_under = most_recent_budget.amount - sum([exp.cost for exp in exps])
                    most_recent_budget.save()

                    # calculate budgets from mrb_date through yesterday (can't set
                    # over/unders for today yet, so today's over/under gets calc'd tomorrow)
                    number_of_days = (now().date() - mrb_date).days
                    # budgets up to today; new_budgets[0] is oldest (day after mrb_date)
                    for i in range(1, number_of_days):
                        b = budget_for_specific_day(emp, mrb_date+timedelta(i))
                        exps_sum = expenditures_sum_for_specific_day(emp, mrb_date+timedelta(i))
                        budget_object, created = Budget.objects.update_or_create(owner=emp,
                                                                                 date=mrb_date+timedelta(i),
                                                                                 defaults={'amount': b,
                                                                                           'over_under': b-exps_sum}
                        )
                    # still want to set the budget _amount_ for today
                    budget, created = Budget.objects.update_or_create(owner=emp,
                                                                      date=now().date(),
                                                                      defaults={'amount': budget_for_specific_day(emp, now().date())}
                    )

                    exps = Expenditure.objects.filter(owner=emp, date=now().date())
                    exps_sum = sum([exp.cost for exp in exps])
                    current_budget = budget.amount - exps_sum
                    cache.set(emp_cache_key+'current_budget', current_budget)

        try:
            yesterday_budget = Budget.objects.get(owner=emp, date=now().date()-timedelta(1))
            # negative over_under means they went over
            if current_budget < 0:
                negative_budget = True
            else:
                negative_budget = False
            # not sure why I had this here
            # if yesterday_budget.amount < 0:
            #     yesterday_budget_negative = True

            # negative over_under means they went over
            #
            # this was an elif before
            if yesterday_budget.over_under < 0:
                over = -1
            elif yesterday_budget.over_under > 0:
                over = 1
            elif yesterday_budget.over_under == 0:
                over = 'on budget'
            return render(request, 'demo-budget.html', {'budget': pretty_dollar_amount(current_budget),
                                                        'over': over,
                                                        'negative_budget': negative_budget,
                                                        # 'yesterday_budget_negative': yesterday_budget_negative,
                                                        'over_under_amount': abs(yesterday_budget.over_under)})
        except:
            return render(request, 'demo-budget.html', {'budget': pretty_dollar_amount(current_budget)})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def budget_history(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    all_budgets = Budget.objects.filter(owner=emp)

    return render(request, 'demo-budget_history.html', {'budgets': all_budgets})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def reset_budgets(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    if request.method == 'POST':
        start_date = emp.signup_date
        budget_today = update_budgets(emp, start_date)

        # update cached budget
        today_expends = cache.get(emp_cache_key+'today_expends')
        if not today_expends:
            today_expends = Expenditure.objects.filter(owner=emp, date=now().date())
            cache.set(emp_cache_key+'today_expends', today_expends)
        expends_sum = sum([exp.cost for exp in today_expends])

        current_budget = budget_today - expends_sum
        cache.set(emp_cache_key+'current_budget', current_budget)

        return redirect('/demo/budget/')

    else:
        return render(request, 'demo-reset_budget.html')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def weekly_budget(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    # if user is new, send to new-user-setup
    if emp.new_user:
        return redirect('/demo/new-user-setup/')

    else:
        wk_budget = cache.get(emp_cache_key+'weekly_budget')
        if not wk_budget:
            wk_budget = weekly_budget_simple(emp)
            cache.set(emp_cache_key+'weekly_budget', wk_budget)
        return render(request, 'demo-weekly_budget.html', {'weekly_budget': pretty_dollar_amount(wk_budget)})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def monthly_budget(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    # if user is new, send to new-user-setup
    if emp.new_user:
        return redirect('/demo/new-user-setup/')

    else:
        return render(request, 'demo-monthly_budget.html', {'monthly_budget': pretty_dollar_amount(monthly_budget_amount(emp))})
