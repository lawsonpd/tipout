from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta

from tipout.models import Tip, EnterTipsForm, Paycheck, Employee, Expense, Expenditure
from budget_utils import daily_budget
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
        # avg_daily_tips = pretty_dollar_amount(emp.init_avg_daily_tips)
        # avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned(tip_values))
        budget = daily_budget(emp)
        return render(request, 'budget.html', {'budget': budget})
