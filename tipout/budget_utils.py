from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from custom_auth.models import TipoutUser
from tipout.models import Paycheck, Employee, Expense, Expenditure, Tip, Budget
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
    if amount < 0:
        return '-$' + '{0:.2f}'.format(abs(amount))
    else:
        return '$' + '{0:.2f}'.format(amount)

def balancer(over_unders):
    return sum(map(lambda x: float(x)/7, over_unders))

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
                                                  'over_under': budget_amount-expends_sum}
        )
        # try:
        #     budget = Budget.objects.get(owner=emp,
        #                                 date=date+timedelta(i))
        #     budget.amount=budget_amount
        #     budget.over_under=budget_amount-expends_sum
        #     budget.save()
        # except:
        #     budget = Budget.objects.create(owner=emp,
        #                                    date=date+timedelta(i),
        #                                    amount=budget_amount,
        #                                    over_under=budget_amount-expends_sum)
    # we still want to recalculate the budget _amount_ for today
    # if the budget hasn't been created yet, create it
    budget_today, created = Budget.objects.update_or_create(owner=emp,
                                                   date=now().date(),
                                                   defaults={'amount': today_budget(emp)}
    )
    # try:
    #     budget_today = Budget.objects.get(owner=emp, date=now().date())
    #     budget_today.amount = today_budget(emp)
    #     budget_today.save()
    # except:
    #     budget_today = Budget.objects.create(owner=emp, date=now().date(), amount=today_budget(emp))

    return budget_today.amount

def today_budget(emp):
    '''
    Calculate budget for today.
    '''
    expenses = Expense.objects.filter(owner=emp)
    expense_cost_for_today = daily_expense_cost(expenses) # sum([ exp.cost for exp in expenses ]) / 30

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
    return tips_for_day + daily_avg_from_paycheck(paycheck_amts) - expense_cost_for_today - expenditures_for_day + Decimal(balancer(over_unders))

def budget_for_specific_day(emp, date):
    '''
    date must be datetime format
    '''
    expenses = Expense.objects.filter(owner=emp, date_added__gte=date)
    expense_cost_for_today = daily_expense_cost(expenses) # sum([ exp.cost for exp in expenses ]) / 30

    # expenditures for the day
    expenditures_for_day_query = Expenditure.objects.filter(owner=emp, date=date)
    expenditures_for_day = sum([ exp.cost for exp in expenditures_for_day_query ])

    # get tips for last 30 days before date parameter
    # not sure if order_by is ascending or descending
    # --> '-date_earned' is descending (newest first)
    tips = Tip.objects.filter(owner=emp, date_earned__lte=(date)).order_by('-date_earned')[:30]
    tip_values = [ tip.amount for tip in tips ]

    # user's paychecks from last 30 days
    recent_paychecks = Paycheck.objects.filter(owner=emp,
                                               date_earned__gt=(date-timedelta(30)),
                                               date_earned__lte=(date)
                                               )
    paycheck_amts = [ paycheck.amount for paycheck in recent_paychecks ]
    # daily_avg_from_paycheck = (sum(paycheck_amts) / len(paycheck_amts))

    # getting over/unders
    past_budgets = Budget.objects.filter(owner=emp, date__lt=date).order_by('-date')[:7]
    over_unders = [budget.over_under for budget in past_budgets]

    if now().date() - emp.signup_date <= timedelta(30):
        tips_for_day = tips_available_per_day_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date)
    else:
        tips_for_day = tips_available_per_day(tip_values)
    return tips_for_day + daily_avg_from_paycheck(paycheck_amts) - expense_cost_for_today - expenditures_for_day + Decimal(balancer(over_unders))

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
