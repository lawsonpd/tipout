from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta

from tipout.models import Tip, EnterTipsForm, Paycheck, Employee, Expense, Expenditure
from budget_utils import (avg_daily_tips_earned,
                          avg_daily_tips_earned_initial,
                          tips_available_per_day_initial,
                          tips_available_per_day,
                          daily_avg_from_paycheck,
                          pretty_dollar_amount
                         )
from custom_auth.models import TipoutUser

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
        # expenses, daily expense cost - assuming every expense is paid monthly
        expenses = Expense.objects.filter(owner=emp)
        daily_expense_cost = sum([ exp.cost for exp in expenses ]) / 30

        # expenditures for the day
        expenditures_today_query = Expenditure.objects.filter(owner=emp, date=now().date())
        expenditures_today = sum([ exp.cost for exp in expenditures_today_query ])

        # get tips for last 30 days
        # not sure if order_by is ascending or descending
        # --> '-date_earned' is descending (newest first)
        tips = Tip.objects.filter(owner=emp).order_by('-date_earned')[:30]
        tip_values = [ tip.amount for tip in tips ]

        # user's paychecks from last 30 days
        recent_paychecks = Paycheck.objects.filter(owner=emp, date_earned__gt=(now().date()-timedelta(30)))
        paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]
        # daily_avg_from_paycheck = (sum(paycheck_amts) / len(paycheck_amts))

        if (now().date() - emp.signup_date).days <= 30:
            budget = tips_available_per_day_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date) + daily_avg_from_paycheck(paycheck_amts) - daily_expense_cost - expenditures_today
            budget_formatted = pretty_dollar_amount(budget)
            avg_daily_tips = pretty_dollar_amount(emp.init_avg_daily_tips)
            return render(request, 'budget.html', {'avg_daily_tips': avg_daily_tips, 'budget': budget_formatted})

        else:
            budget = tips_available_per_day(tip_values) + daily_avg_from_paycheck(paycheck_amts) - daily_expense_cost - expenditures_today
            budget_formatted = pretty_dollar_amount(budget)
            avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned(tip_values))
            return render(request, 'budget.html', {'avg_daily_tips': avg_daily_tips, 'budget': budget_formatted})
