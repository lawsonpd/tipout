from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control

from tipout.models import Tip, Paycheck, Employee, Expense, Expenditure, Budget
from budget_utils import today_budget, pretty_dollar_amount, expenditures_sum_for_specific_day, budget_for_specific_day
from custom_auth.models import TipoutUser

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
    emp = Employee.objects.get(user=u)

    # if user is new, send to new-user-setup
    if emp.new_user:
        return redirect('/new-user-setup/')

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

        current_budget = cache.get('current_budget')

        if not current_budget:
            try:
                budget = Budget.objects.get(owner=emp, date=now().date())
                exps = Expenditure.objects.filter(owner=emp, date=now().date())
                exps_sum = sum([exp.cost for exp in exps])
                current_budget = budget.amount - exps_sum
                cache.set('current_budget', current_budget)

            except:
                try:
                    yesterday_budget = Budget.objects.get(owner=emp, date=now().date()-timedelta(1))
                    yesterday_exps = Expenditure.objects.filter(owner=emp, date=now().date()-timedelta(1))
                    yesterday_budget.over_under = yesterday_budget.amount - sum([exp.cost for exp in yesterday_exps])
                    yesterday_budget.save()
                    budget = Budget(owner=emp,
                                    date=now().date(),
                                    amount=today_budget(emp))
                    budget.save()

                    exps = Expenditure.objects.filter(owner=emp, date=now().date())
                    exps_sum = sum([exp.cost for exp in exps])
                    current_budget = budget.amount - exps_sum
                    cache.set('current_budget', current_budget)

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
                        budget_object = Budget(owner=emp,
                                               date=mrb_date+timedelta(i),
                                               amount=b,
                                               over_under=b-exps_sum)
                        budget_object.save()
                    # still want to set the budget _amount_ for today
                    budget = Budget(owner=emp,
                                    date=now().date(),
                                    amount=today_budget(emp))
                    budget.save()

            exps = Expenditure.objects.filter(owner=emp, date=now().date())
            exps_sum = sum([exp.cost for exp in exps])
            current_budget = budget.amount - exps_sum
            cache.set('current_budget', current_budget)

        yesterday_budget = Budget.objects.get(owner=emp, date=now().date()-timedelta(1))
        # negative over_under means they went over
        if yesterday_budget.over_under < 0:
            over = True
        elif yesterday_budget.over_under > 0:
            over = False
        else:
            over = 0

        return render(request, 'budget.html', {'budget': pretty_dollar_amount(current_budget),
                                               'over': over,
                                               'over_under_amount': abs(yesterday_budget.over_under)})
