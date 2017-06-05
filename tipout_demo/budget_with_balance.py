from django.utils.timezone import now, timedelta
from django.core.cache import cache

from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

from tipout_demo.models import Balance, Expenditure, Expense, Budget
from tipout_demo.budget_utils import daily_expense_cost, ou_contribs, budget_corrector, expenditures_sum_for_specific_day
from decimal import Decimal

def budget_for_specific_day(emp, date):
    '''
    date must be datetime format
    '''
    expenses = Expense.objects.filter(owner=emp, date_added__gte=date)
    expense_cost_for_today = daily_expense_cost(expenses) # sum([ exp.cost for exp in expenses ]) / 30

    emp_balance = Balance.objects.get(owner=emp)
    balance = emp_balance.amount

    # getting over/unders
    past_budgets = Budget.objects.filter(owner=emp, date__lt=date).order_by('-date')[:7]
    over_unders = [budget.over_under for budget in past_budgets]
    ous = Decimal(budget_corrector(over_unders))

    return balance/30 - expense_cost_for_today + ous

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
                                                            defaults={'amount': budget_for_specific_day(emp, now().date())}
    )

    return budget_today.amount

def weekly_budget_simple(emp):
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    balance = cache.get(emp_cache_key+'balance')
    if not balance:
        balance = Balance.objects.get(owner=emp)
        cache.set(emp_cache_key+'balance', balance)

    if balance.amount == 0:
        balance_amt = 0
    else:
        balance_amt = (balance.amount / 30 * 7)

    expenses = cache.get(emp_cache_key+'expenses')
    if not expenses:
        expenses = Expense.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expenses', expenses)

    expense_cost_per_day = daily_expense_cost(expenses)

    over_unders = Decimal(ou_contribs(emp))

    return balance_amt - (expense_cost_per_day * 7) + over_unders

