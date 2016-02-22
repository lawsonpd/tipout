def calculate_tips_avg_initial(init_avg_daily_tips, tips_so_far, signup_date):
    # assume 1 month period before using actual tips to calculate average
    #
    # avg = (init_avg * (today_date - signup_date)
    #                 + sum(tips_so_far))
    #                 / 30
    pass

def calculate_tips_avg(tips):
    # calculate tips for last 30 days
    return sum(tips) / 30
