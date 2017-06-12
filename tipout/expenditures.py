from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import permission_required
from django.utils.timezone import now
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from string import strip

from tipout.models import Employee, Expenditure, EnterExpenditureForm, EditExpenditureForm, Balance
from budget_with_balance import update_budgets, weekly_budget_simple
from budget_utils import pretty_dollar_amount
from custom_auth.models import TipoutUser

from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def enter_expenditure(request):
    '''
    If POST, admit and process form. Otherwise, show blank form.
    '''
    if request.method == 'POST':
        form = EnterExpenditureForm(request.POST)
        if form.is_valid():
            # process form data
            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)
            exp_data = form.cleaned_data

            emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

            expends = cache.get(emp_cache_key+'expends')
            if not expends:
                expends = Expenditure.objects.filter(owner=emp)
                cache.set(emp_cache_key+'expends', expends)

            if expends.filter(date=exp_data['date'], note=exp_data['note'].lower()).exists():
                return render(request,
                              'enter_expenditure.html',
                              {'form': EnterExpenditureForm(initial={'date': exp_data['date'],
                                                                     'cost': exp_data['cost']}),
                               'error_message': 'An expenditure for today with that note already exists.'}
                              )
            if exp_data['date'] > now().date():
                return render(request,
                              'enter_expenditure.html',
                              {'form': EnterExpenditureForm(initial={'note': exp_data['note'],
                                                                     'cost': exp_data['cost']}),
                               'error_message': "Please enter a date that isn't in the future."}
                              )
            else:
                e = Expenditure.objects.create(owner=emp,
                                               cost=exp_data['cost'],
                                               date=exp_data['date'],
                                               note=exp_data['note']
                )

                expends = Expenditure.objects.filter(owner=emp)
                cache.set(emp_cache_key+'expends', expends)

                # update today_expends if expend added is for today
                if e.date == now().date():
                    today_expends = expends.filter(date=now().date())
                    cache.set(emp_cache_key+'today_expends', today_expends)

                # update balance
                balance = Balance.objects.get(owner=emp)
                balance.amount -= e.cost
                balance.save()

                # update balance cache
                cache.set(emp_cache_key+'balance', balance)

                # update_budgets return today's budget amount
                budget_today = update_budgets(emp, e.date)

                # update cached budget
                today_expends = cache.get(emp_cache_key+'today_expends')
                if not today_expends:
                    today_expends = Expenditure.objects.filter(owner=emp, date=now().date())
                    cache.set(emp_cache_key+'today_expends', today_expends)

                expends_sum = sum([exp.cost for exp in today_expends])
                current_budget = budget_today - expends_sum
                cache.set(emp_cache_key+'current_budget', current_budget)

                wk_budget = weekly_budget_simple(emp)
                cache.set(emp_cache_key+'weekly_budget', wk_budget)

                return redirect('/budget/')
    else:
        return render(request,
                      'enter_expenditure.html',
                      {'form': EnterExpenditureForm(initial={'date': now().date()})}
                      )

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenditures(request):
    '''
    Default expenditures page show TODAY'S expenditures.
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    today_expends = cache.get(emp_cache_key+'today_expends')
    if not today_expends:
        today_expends = Expenditure.objects.filter(owner=emp, date=now().date())
        cache.set(emp_cache_key+'today_expends', today_expends)

    return render(request, 'expenditures.html', {'exps': today_expends})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def spending_profile(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expends = cache.get(emp_cache_key+'expends')
    if not expends:
        expends = Expenditure.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expends', expends)

    expends_sum = sum([exp.cost for exp in expends])
    days_as_user = (now().date() - emp.signup_date).days

    if len(expends) == 0:
        avg_expend = 0
    else:
        avg_expend = expends_sum / len(expends)
    avg_daily_spending = expends_sum / days_as_user

    return render(request, 'spending_profile.html', {'avg_expend': pretty_dollar_amount(avg_expend), 'avg_daily_spending': pretty_dollar_amount(avg_daily_spending)})

# @login_required(login_url='/login/')
# @require_http_methods(['POST'])
# def delete_expenditure(request, *args):
#     exp = args[0].replace('-', ' ')
#
#     if request.method == 'POST':
#         u = TipoutUser.objects.get(email=request.user)
#         emp = Employee.objects.get(user=u)
#
#         es = Expenditure.objects.filter(owner=emp).filter(date=now().date())
#         for exp in es:
#             if strip(exp.get_absolute_url(), '/') == args[0]:
#                 e = exp
#         e.delete()
#         return redirect('/expenditures/')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['POST'])
def delete_expenditure(request, exp, *args):
    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

        expends = cache.get(emp_cache_key+'expends')
        if not expends:
            expends = Expenditure.objects.filter(owner=emp)
            cache.set(emp_cache_key+'expends', expends)

        exp_to_delete = expends.get(pk=exp)
        exp_date = exp_to_delete.date
        # for exp in es:
        #     if strip(exp.get_absolute_url(), '/') == args[0]:
        #         e = exp

        # update balance before deleting expend
        balance = Balance.objects.get(owner=emp)
        balance.amount += exp_to_delete.cost
        balance.save()

        # update balance cache
        cache.set(emp_cache_key+'balance', balance)

        exp_to_delete.delete()

        expends = Expenditure.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expends', expends)

        # update today_expends if expend was for today
        if exp_date == now().date():
            today_expends = expends.filter(date=now().date())
            cache.set(emp_cache_key+'today_expends', today_expends)

        # update_budgets return today's budget amount
        budget_today = update_budgets(emp, exp_date)

        # update cached budget
        today_expends = cache.get(emp_cache_key+'today_expends')
        if not today_expends:
            today_expends = Expenditure.objects.filter(owner=emp, date=now().date())
            cache.set(emp_cache_key+'today_expends', today_expends)
        expends_sum = sum([exp.cost for exp in today_expends])

        current_budget = budget_today - expends_sum
        cache.set(emp_cache_key+'current_budget', current_budget)

        wk_budget = weekly_budget_simple(emp)
        cache.set(emp_cache_key+'weekly_budget', wk_budget)

        return redirect('/expenditures/')

# To edit an expenditure, you'll have to use pk to identify it, since the note and amount could change.
# This would effectively be deleting an expenditure and creating a new one, which might be enough anyway.
#
@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def edit_expenditure(request, exp, *args):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expends = cache.get(emp_cache_key+'expends')
    if not expends:
        expends = Expenditure.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expends', expends)

    exp_to_edit = expends.get(pk=exp)

    if request.method == 'POST':
        form = EditExpenditureForm(request.POST)
        if form.is_valid():
            exp_data = form.cleaned_data

            exp_to_edit.cost = exp_data['cost']
            exp_to_edit.note = exp_data['note']
            exp_to_edit.date = exp_data['date']
            exp_to_edit.save()

            expends = Expenditure.objects.filter(owner=emp)
            cache.set(emp_cache_key+'expends', expends)

            # update today_expends if expend was for today
            if exp_to_edit.date == now().date():
                today_expends = expends.filter(date=now().date())
                cache.set(emp_cache_key+'today_expends', today_expends)

            # update balance
            balance = Balance.objects.get(owner=emp)
            balance.amount -= exp_data['cost'] - exp_to_edit.cost
            balance.save()

            # update balance cache
            cache.set(emp_cache_key+'balance', balance)

            # update_budgets return today's budget amount
            budget_today = update_budgets(emp, exp_to_edit.date)

            # update cached budget
            today_expends = cache.get(emp_cache_key+'today_expends')
            if not today_expends:
                today_expends = Expenditure.objects.filter(owner=emp, date=now().date())
                cache.set(emp_cache_key+'today_expends', today_expends)
            expends_sum = sum([exp.cost for exp in today_expends])

            current_budget = budget_today - expends_sum
            cache.set(emp_cache_key+'current_budget', current_budget)

            wk_budget = weekly_budget_simple(emp)
            cache.set(emp_cache_key+'weekly_budget', wk_budget)

            return redirect('/expenditures/')
    else:
        form = EditExpenditureForm(initial={'note': exp_to_edit.note,
                                            'cost': exp_to_edit.cost,
                                            'date': exp_to_edit.date
                                           }
                                  )
        return render(request, 'edit_expenditure.html', {'form': form, 'exp': exp_to_edit})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenditures_archive(request, *args):
    '''
    Shows a list of years
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expends = cache.get(emp_cache_key+'expends')
    if not expends:
        expends = Expenditure.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expends', expends)

    all_years = [e.date.year for e in expends]
    years = set(all_years)
    return render(request, 'expenditures_archive.html', {'years': years})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenditures_year_archive(request, year, *args):
    '''
    Shows a list of months
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expends = cache.get(emp_cache_key+'expends')
    if not expends:
        expends = Expenditure.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expends', expends)

    # all_months = [e.month_name for e in Expenditure.objects.filter(owner=u)
    #                            if e.date.year == year]
    # months = set(all_months)
    dates = expends.filter(date__year=year).dates('date', 'month')
    months = [date.month for date in dates]
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'months': months})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenditures_month_archive(request, year, month, *args):
    '''
    Shows a list of days
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expends = cache.get(emp_cache_key+'expends')
    if not expends:
        expends = Expenditure.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expends', expends)

    dates = expends.filter(date__year=year,
                           date__month=month).dates('date', 'day')
    days = [date.day for date in dates]
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'month': month,
                                                         'days': days})

@cache_control(private=True)
@login_required(login_url='/login/')
def expenditures_day_archive(request, year, month, day, *args):
    '''
    Shows a list of expenditures
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expends = cache.get(emp_cache_key+'expends')
    if not expends:
        expends = Expenditure.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expends', expends)

    day_expends = expends.filter(date__year=year,
                                 date__month=month,
                                 date__day=day)
    # expends_notes = [date.note for exp in expends]
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'month': month,
                                                         'day': day,
                                                         'exps': day_expends})

@cache_control(private=True)
@login_required(login_url='/login/')
def expenditure_detail(request, year, month, day, exp, *args):
    '''
    Shows details about a particular expenditure
    '''
    exp_note = exp.replace('-', ' ')

    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email, md5).hexdigest()

    expends = cache.get(emp_cache_key+'expends')
    if not expends:
        expends = Expenditure.objects.filter(owner=emp)
        cache.set(emp_cache_key+'expends', expends)

    exp = expends.get(date__year=year,
                      date__month=month,
                      date__day=day,
                      note=exp_note)
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'month': month,
                                                         'day': day,
                                                         'exp': exp})
