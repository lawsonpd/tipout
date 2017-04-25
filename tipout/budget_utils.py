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
    '''
    Should be passed budgets, expenditures:
    budgets is List of budgets for each of past 7 days.
    expenditures is List of expenditures for each of past 7 days.
    '''
    return sum([float(over_unders[i]) / 7 for i in range(len(over_unders))])

def daily_budget(emp):
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
        tips_for_day = tips_available_per_day_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date)
    else:
        tips_for_day = tips_available_per_day(tip_values)
    budget = tips_for_day + daily_avg_from_paycheck(paycheck_amts) - daily_expense_cost - expenditures_today
    return pretty_dollar_amount(budget)
