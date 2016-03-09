from datetime import date

def calc_tips_avg_initial(init_avg_daily_tips, tips_so_far, signup_date):
    # assume 1 month period before using actual tips to calculate average
    #
    # avg = (init_avg * (today_date - signup_date)
    #                 + sum(tips_so_far))
    #                 / 20
    # using 20 days because i'm assuming 5 work days per week (so 20 per mo.)
    days_so_far = (date.today() - signup_date).days
    return (init_avg_daily_tips * (20 - days_so_far) + sum(tips_so_far)) / 20

def calc_tips_avg(tips):
    # calculate tips for last 30 days
    return sum(tips) / 20
