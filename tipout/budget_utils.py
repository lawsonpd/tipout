from django.utils.timezone import now, timedelta
from custom_auth.models import TipoutUser
from tipout.models import Paycheck, Employee, Expense, Expenditure, Tip, Budget, Balance, OtherFunds
from decimal import Decimal

def avg_daily_tips_earned_initial(init_avg_daily_tips, tips_so_far, signup_date):
    '''
    This calculates what a user makes on average from tips *on the days they work*,
    so we're dividing by 21.3 assuming 21.3 work days per month.
    '''
    days_so_far = (now().date() - signup_date).days
    days_left_in_month = 30 - days_so_far
    days_left_to_work = days_left_in_month * 0.71
    days_worked_so_far = len(tips_so_far)
    if len(tips_so_far) > 0:
        tips_avg_so_far = Decimal(sum(tips_so_far) / len(tips_so_far))
    else:
        tips_avg_so_far = 0
    # old way, which didn't work correctly:
    # return (init_avg_daily_tips * Decimal((30 - days_so_far) * .71)) / Decimal(21.3)
    # return ((init_avg_daily_tips * Decimal((30 - len(tips_so_far)) * .71)) / Decimal(21.3)) + ((tips_avg_so_far * Decimal(len(tips_so_far)* .71)) / Decimal(21.3))
    return ((days_left_in_month * float(init_avg_daily_tips) * 0.71) + float(sum(tips_so_far))) \
            / (days_left_to_work + days_worked_so_far)

def avg_daily_tips_earned(tips):
    '''
    List -> Int
    '''
    # calculate tips for last 30 days
    if tips:
        return sum(tips) / Decimal(21.3)
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
    if amount < 0:
        return '-$' + '{0:.2f}'.format(abs(amount))
    else:
        return '$' + '{0:.2f}'.format(amount)

def budget_corrector(over_unders):
    return sum(map(lambda x: float(x)/7, over_unders))

def spendable(emp):
    return  (100 - emp.savings_percent) / 100

def update_budgets(emp, date):
    '''
    date is the date to *start* with. go from date through yesterday (now()date() - timedelta(1)).
    '''
    # starting_budget = Budget.objects.filter(owner=emp, date=date)

    # calculate budgets from date through yesterday (can't set
    # over/unders for today yet, so today's over/under gets calc'd tomorrow)
    number_of_days = (now().date() - date).days
    for i in range(number_of_days):
        budget_amount = budget_for_specific_day(emp, date+timedelta(i))
        expends_sum = expenditures_sum_for_specific_day(emp, date+timedelta(i))
        Budget.objects.update_or_create(owner=emp,
                                        date=date+timedelta(i),
                                        defaults={'amount': budget_amount,
                                                  'over_under': budget_amount - expends_sum}
        )

    # we still want to recalculate the budget _amount_ for today
    # if the budget hasn't been created yet, create it
    budget_today, created = Budget.objects.update_or_create(owner=emp,
                                                            date=now().date(),
                                                            defaults={'amount': today_budget(emp)}
    )

    return budget_today.amount

def today_budget(emp):
    '''
    Calculate budget for today.
    '''
    expenses = Expense.objects.filter(owner=emp)
    expense_cost_for_today = daily_expense_cost(expenses) # sum([ exp.cost for exp in expenses ]) / 30

    # expenditures for the day
    # expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=now().date())
    # expenditures_for_day = sum([ exp.cost for exp in expenditures_for_day_query ])

    # get tips for last 30 days
    # not sure if order_by is ascending or descending
    # --> '-date_earned' is descending (newest first)
    tips = Tip.objects.filter(owner=emp, date_earned__gte=now().date()-timedelta(30))
    tip_values = [ tip.amount for tip in tips ]
    if (now().date() - emp.signup_date).days <= 30:
        tips_for_day = tips_available_per_day_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date) * spendable(emp)
    else:
        tips_for_day = tips_available_per_day(tip_values) * spendable(emp)

    # user's paychecks from last 30 days
    recent_paychecks = Paycheck.objects.filter(owner=emp,
                                               date_earned__gte=(now().date()-timedelta(30)))
    paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]
    daily_from_paycheck = daily_avg_from_paycheck(paycheck_amts) * spendable(emp)

    # getting over/unders
    past_budgets = Budget.objects.filter(owner=emp, date__lt=now().date()).order_by('-date')[:7]
    over_unders = [budget.over_under for budget in past_budgets]
    ous = Decimal(budget_corrector(over_unders))

    return tips_for_day + daily_from_paycheck - expense_cost_for_today + ous

def budget_for_specific_day(emp, date):
    '''
    date must be datetime format
    '''
    expenses = Expense.objects.filter(owner=emp, date_added__gte=date)
    expense_cost_for_today = daily_expense_cost(expenses) # sum([ exp.cost for exp in expenses ]) / 30

    # expenditures for the day
    # expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=date)
    # expenditures_for_day = sum([ exp.cost for exp in expenditures_for_day_query ])

    # get tips for last 30 days before date parameter
    # not sure if order_by is ascending or descending
    # --> '-date_earned' is descending (newest first)
    tips = Tip.objects.filter(owner=emp, date_earned__lte=(date), date_earned__gte=(date-timedelta(30)))
    tip_values = [ tip.amount for tip in tips ]
    if now().date() - emp.signup_date <= timedelta(30):
        tips_for_day = tips_available_per_day_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date) * spendable(emp)
    else:
        tips_for_day = tips_available_per_day(tip_values) * spendable(emp)

    # user's paychecks from last 30 days
    recent_paychecks = Paycheck.objects.filter(owner=emp,
                                               date_earned__gte=(date-timedelta(30)),
                                               date_earned__lte=(date)
                                               )
    paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]
    daily_from_paycheck = daily_avg_from_paycheck(paycheck_amts) * spendable(emp)

    # getting over/unders
    past_budgets = Budget.objects.filter(owner=emp, date__lt=date).order_by('-date')[:7]
    over_unders = [budget.over_under for budget in past_budgets]
    ous = Decimal(budget_corrector(over_unders))

    return tips_for_day + daily_from_paycheck - expense_cost_for_today + ous

def daily_expense_cost(expenses):
    dailies = sum([e.cost for e in expenses if e.frequency == 'DAILY'])
    weeklies = sum([e.cost for e in expenses if e.frequency == 'WEEKLY'])
    bi_weeklies = sum([e.cost for e in expenses if e.frequency == 'BI-WEEKLY'])
    monthlies = sum([e.cost for e in expenses if e.frequency == 'MONTHLY'])
    annuallies = sum([e.cost for e in expenses if e.frequency == 'ANNUALLY'])

    return dailies + (weeklies/7) + (bi_weeklies/14) + (monthlies/30) + (annuallies/365)

def expenditures_sum_for_specific_day(emp, date):
    expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=date)
    return sum([ exp.cost for exp in expenditures_for_day_query ])

def weekly_budget_amount(emp):
    recent_paychecks = Paycheck.objects.filter(owner=emp, date_earned__gte=(now().date()-timedelta(30)))
    paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]
    # divide by 4 to get an estimate average contribution from paychecks for 1 week
    paycheck_avgd_to_add = sum(paycheck_amts/4) * spendable(emp)

    # tips = Tip.objects.filter(owner=emp).order_by('-date_earned')[:30]
    tips = Tip.objects.filter(owner=emp, date_earned__gte=(now().date()-timedelta(30)))
    tip_values = [ tip.amount for tip in tips ]
    tips_avg_to_add = (sum(tip_values)/30) * 7 * spendable(emp)

    expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=now().date())
    expenditures_for_day = sum([ exp.cost for exp in expenditures_for_day_query ])

    expenses = Expense.objects.filter(owner=emp)
    expense_cost_for_week = daily_expense_cost(expenses) * 7

    past_budgets = Budget.objects.filter(owner=emp, date__lt=now().date()).order_by('-date')[:6]
    over_unders = float(sum([budget.over_under for budget in past_budgets]))

    return tips_avg_to_add + paycheck_avg_to_add - expense_cost_for_week - expenditures_for_day - over_unders

def monthly_budget_amount(emp):
    '''
    Budget for month should probably rely on averages and not actual values.
    '''
    recent_paychecks = Paycheck.objects.filter(owner=emp, date_earned__gt=(now().date()-timedelta(31)))
    paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]

    # tips = Tip.objects.filter(owner=emp).order_by('-date_earned')[:30]
    tips = Tip.objects.filter(owner=emp, date_earned__gt=(now().date()-timedelta(31)))
    tip_values = [ tip.amount for tip in tips ]

    expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=now().date())
    expenditures_for_day = sum([ exp.cost for exp in expenditures_for_day_query ])

    expenses = Expense.objects.filter(owner=emp)
    expense_cost_for_today = daily_expense_cost(expenses)

    past_budgets = Budget.objects.filter(owner=emp, date__lt=now().date()).order_by('-date')[:30]
    over_unders = [budget.over_under for budget in past_budgets]

    return (sum(tip_values) * spendable(emp)) + (sum(paycheck_amts) * spendable(emp)) - (expense_cost_for_today * 30) - expenditures_for_day - sum(over_unders)

def weekly_budget_simple(emp):
    recent_paychecks = Paycheck.objects.filter(owner=emp, date_earned__gte=(now().date()-timedelta(30)))
    paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]
    daily_from_paycheck = daily_avg_from_paycheck(paycheck_amts) * spendable(emp)

    tips = Tip.objects.filter(owner=emp, date_earned__gte=(now().date()-timedelta(30)))
    tip_values = [ tip.amount for tip in tips ]
    if (now().date() - emp.signup_date).days <= 30:
        tips_for_day = tips_available_per_day_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date) * spendable(emp)
    else:
        tips_for_day = tips_available_per_day(tip_values) * spendable(emp)

    expenses = Expense.objects.filter(owner=emp)
    expense_cost_per_day = daily_expense_cost(expenses)

    expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=now().date())
    expenditures_for_day = sum([ exp.cost for exp in expenditures_for_day_query ])

    over_unders = Decimal(ou_contribs(emp))

    return (tips_for_day * 7) + (daily_from_paycheck * 7) - (expense_cost_per_day * 7) - expenditures_for_day + over_unders

def ou_contribs(emp):
    budgets = Budget.objects.filter(owner=emp, date__lt=now().date()).order_by('-date')[:7]
    # [0] in return is most recent
    ous = []
    for i in xrange(len(budgets)):
        ous.append(float(budgets[i].over_under) / 7.0 * (7-i))
    return sum(ous)
