from custom_auth import TipoutUser
from django.utils.timezone import now, timedelta
from tipout.models import Paycheck, Employee, Expense, Expenditure, Tip
from decimal import Decimal

def avg_daily_tips_earned_initial(init_avg_daily_tips, tips_so_far, signup_date):
    '''
    This calculates what a user makes on average from tips *on the days they work*,
    so we're dividing by 21.3 assuming 21.3 work days per month.
    '''
    days_so_far = (now().date() - signup_date).days
    return (init_avg_daily_tips * Decimal((30 - days_so_far) * .71) + sum(tips_so_far)) / Decimal(21.3)

def avg_daily_tips_earned(tips):
    '''
    List -> Int
    '''
    # calculate tips for last 30 days
    if tips:
        return sum(tips) / 21.3
    else:
        return 0

def tips_available_per_day_initial(init_avg_daily_tips, tips_so_far, signup_date):
    '''
    This is what we want to use to calculate how much a user has *available* each day
    from their tips as part of their budget.
    We divide by 30 instead of 21.3 because we're not interested in how much they *make*
    on average each day they work, but instead how much they *have* daily based on
    the total amount earned.
    '''
    days_so_far = (now().date() - signup_date).days
    return (init_avg_daily_tips * Decimal((30 - days_so_far) * .71) + sum(tips_so_far)) / Decimal(30)

def tips_available_per_day(tips):
    '''
    This is what we want to use to calculate how much a user has *available* each day
    from their tips as part of their budget.
    We divide by 30 instead of 21.3 because we're not interested in how much they *make*
    on average each day they work, but instead how much they *have* daily based on
    the total amount earned.
    '''
    return sum(tips) / 30

def daily_avg_from_paycheck(paycheck_amts):
    # assuming paychecks are bi-weekly (2/mo)
    # return (sum(paycheck_amts) / len(paycheck_amts)) / 15
    # no need to do this ^
    # simply add up the paychecks from the last 30 days
    return sum(paycheck_amts) / 30

def avg_hourly_wage(tips, paychecks, num_days):
    # will need to call avg_daily_tips and daily_avg_from_paycheck
    #
    # hours from paychecks and hours from tips should be equal
    '''
    total_hours should really be hours in past num_days days
    '''
    total_hours = sum([ tip.hours_worked for tip in tips ])

    return ((avg_daily_tips(tips) + daily_avg_from_paycheck(paychecks)) * num_days) / total_hours

def pretty_dollar_amount(amount):
  return '$' + '{0:.2f}'.format(amount)

def balancer(over_unders):
    return sum(map(lambda x: float(x)/7, over_unders))

def today_budget(emp):
    '''
    Calculate budget for today.
    '''
    # expenses, daily expense cost - assuming every expense is paid monthly
    expenses = Expense.objects.filter(owner=emp)
    daily_expense_cost = sum([ exp.cost for exp in expenses ]) / 30

    # expenditures for the day
    expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=now().date())
    expenditures_for_day = sum([ exp.cost for exp in expenditures_for_day_query ])

    # get tips for last 30 days
    # not sure if order_by is ascending or descending
    # --> '-date_earned' is descending (newest first)
    tips = Tip.objects.filter(owner=emp).order_by('-date_earned')[:30]
    tip_values = [ tip.amount for tip in tips ]

    # user's paychecks from last 30 days
    recent_paychecks = Paycheck.objects.filter(owner=emp,
                                               date_earned__gt=(now().date()-timedelta(30)))
    paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]
    # daily_avg_from_paycheck = (sum(paycheck_amts) / len(paycheck_amts))

    # getting over/unders
    past_budgets = Budget.objects.filter(owner=emp).order_by('-date')[:7]
    over_unders = [budget.over_under for budget in past_budgets]

    if (now().date() - emp.signup_date).days <= 30:
        tips_for_day = tips_available_per_day_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date)
    else:
        tips_for_day = tips_available_per_day(tip_values)
    return tips_for_day + daily_avg_from_paycheck(paycheck_amts) - daily_expense_cost - expenditures_for_day + balancer(over_unders)

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
