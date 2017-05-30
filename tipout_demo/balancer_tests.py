from tipout_demo.models import DemoEmployee, Paycheck, Tip, Expenditure, Expense
from custom_auth.models import TipoutUser
from django.utils.timezone import now, timedelta
from budget_utils import tips_available_per_day_initial, tips_available_per_day, daily_avg_from_paycheck

'''
Really what gets passed to balancer is the amount under budget for a particular day.
Negative means user was over budget.
'''

# BUDGET REVAMP
# tips daily + paycheck daily - expenses daily - expenditures today + yesterday over/under + balancer
#
# mon     tue     wed     thu     fri
# -10     5       -5      0       -5

def balancer(over_unders):
    return sum(map(lambda x: float(x)/7, over_unders))

def budget_for_specific_day(emp, date):
    '''
    date must be datetime format
    '''
    # expenses, daily expense cost - assuming every expense is paid monthly
    expenses = Expense.objects.filter(owner=emp)
    daily_expense_cost = sum([ exp.cost for exp in expenses ]) / 30

    # expenditures for the day
    expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=date)
    expenditures_for_day = sum([ exp.cost for exp in expenditures_for_day_query ])

    # get tips for last 30 days before date parameter
    # not sure if order_by is ascending or descending
    # --> '-date_earned' is descending (newest first)
    tips = Tip.objects.filter(owner=emp, date_earned__lt=(date + timedelta(1))).order_by('-date_earned')[:30]
    tip_values = [ tip.amount for tip in tips ]

    # user's paychecks from last 30 days
    recent_paychecks = Paycheck.objects.filter(owner=emp,
                                               date_earned__gt=(date-timedelta(30)),
                                               date_earned__lt=(date+timedelta(1))
                                               )
    paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]
    # daily_avg_from_paycheck = (sum(paycheck_amts) / len(paycheck_amts))

    # getting over/unders
    past_budgets = Budget.objects.filter(owner=emp, date__lt=date).order_by('-date')[:7]
    over_unders = [budget.over_under for budget in past_budgets]

    if (now().date() - emp.signup_date).days <= 30:
        tips_for_day = tips_available_per_day_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date)
    else:
        tips_for_day = tips_available_per_day(tip_values)
    return tips_for_day + daily_avg_from_paycheck(paycheck_amts) - daily_expense_cost - expenditures_for_day + balancer(over_unders)

def expenditures_sum_for_specific_day(emp, date):
    expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=date)
    return sum([ exp.cost for exp in expenditures_for_day_query ])

def get_recent_budgets(emp, start_date):
    # budgets for last 7 days
    #
    # start_date is needed if we're calculating budget for, e.g., yesterday
    return [budget_for_specific_day(emp, now().date() - timedelta(i)) for i in range(1,8)]

def get_recent_expenditures(emp):
    # exps for last 7 days
    return []

test_cases = (
    [5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 0],
    [7, 7, 7, 7, 7, 7, 7],
    [1, 1, 1, 1, 1, 1, 1],
    [-5, -5, -5, -5, -5, -5, -5],
    [-10],
    [-10, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, -10],
    [0, 0, 0, 0, 0, -10, 0],
    [0, 0, 0, 0, -10, 0, 0],
    [0, 0, 0, -10, 0, 0, 0],
    [0, 0, -10, 0, 0, 0, 0],
    [0, -10, 0, 0, 0, 0, 0],
    [-10, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
)

u = TipoutUser.objects.get(email='tom@gmail.com')
emp = DemoEmployee.objects.get(user=u)

if __name__ == '__main__':
    for i in range(len(test_cases)):
        print "Test %s:" % i, balancer(test_cases[i])
    print ""
    print "Budget for %s:" % now().date() - timedelta(1), budget_for_specific_day(emp, now().date() - timedelta(1))
