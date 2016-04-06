from datetime import date
from tipout.models import Paycheck

def avg_daily_tips_initial(init_avg_daily_tips, tips_so_far, signup_date):
    # assume 1 month period before using actual tips to calculate average
    #
    # avg = (init_avg * (today_date - signup_date)
    #                 + sum(tips_so_far))
    #                 / 20
    # using 20 days because i'm assuming 5 work days per week (so 20 per mo.)
    days_so_far = (date.today() - signup_date).days
    return (init_avg_daily_tips * (20 - days_so_far) + sum(tips_so_far)) / 20

def avg_daily_tips(tips):
    # calculate tips for last 30 days
    '''
    List -> Int
    '''
    if tips:
        return sum(tips) / len(tips)
    else:
        return 0

def daily_avg_from_paycheck(paychecks):
    # assuming paychecks are bi-weekly (2/mo)
    #
    # should maybe take tip_values array (or similar)
    # instead of user (see avg_daily_tips)

    # paychecks = Paycheck.objects.filter(owner=user)
    paycheck_amts = [ paycheck.amount for paycheck in paychecks ]

    if paycheck_amts:
        return (sum(paycheck_amts) / len(paycheck_amts)) / 15
    else:
        return 0

def avg_hourly_wage(tips, paychecks, num_days):
    # will need to call avg_daily_tips and daily_avg_from_paycheck
    #
    # hours from paychecks and hours from tips should be equal
    '''
    total_hours should really be hours in past num_days days
    '''
    total_hours = sum([ tip.hours_worked for tip in tips ])

    return ((avg_daily_tips(tips)
          + daily_avg_from_paycheck(paychecks))
          * days)
          / total_hours
