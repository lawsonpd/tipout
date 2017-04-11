from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from tipout.models import Customer, Tip, EnterTipsForm, Paycheck, EditPaycheckForm, Expense, Employee, Expenditure, EnterPaycheckForm, EnterExpenditureForm, EnterExpenseForm, EditExpenseForm, NewUserSetupForm
from django.contrib.auth.models import User, Permission
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required


from tipout.budget import avg_daily_tips, avg_daily_tips_initial, daily_avg_from_paycheck
from datetime import date
from string import strip
# from string import lower

from django.conf import settings

import stripe
stripe.api_key = settings.STRIPE_KEYS['secret_key']

@require_http_methods(['GET'])
def home(request):
    '''
    If user is logged in, redirect to '/budget/', else send to home page.
    '''
    if request.user.is_authenticated:
        return HttpResponseRedirect('/budget/')
    else:
        return render(request, 'home.html')

@require_http_methods(['GET', 'POST'])
def register(request, template_name):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user_data = form.cleaned_data

            # create_user automatically saves entry to db
            user = User.objects.create_user(username=user_data['username'],
                                            password=user_data['password1'])
            # create new Employee
            emp = Employee.objects.create(user=user,
                                          new_user=True,
                                          init_avg_daily_tips=0)

            return HttpResponseRedirect('/login/')
        else:
            return render(request, template_name, {'form': form})
    else:
        form = UserCreationForm()
        return render(request, template_name, {'form': form})

@require_http_methods(['GET', 'POST'])
def subscribe(request, template_name):
    if request.method == 'POST':
        u = User.objects.get(username=request.user)
        if request.POST['stripeEmail'] == u.username:
            customer = stripe.Customer.create(
                email = request.POST['stripeEmail'],
                source = request.POST['stripeToken'],
            )

            try:
                stripe_sub = stripe.Subscription.create(
                    customer=customer.id,
                    plan='paid-plan',
                )

            except Exception as e:
                return HttpResponse("There was an error: ", e)

            u = User.objects.get(username=request.user)
            u.user_permissions.add('use_tips',
                                   'use_budget',
                                   'use_paychecks',
                                   'use_expenses',
                                   'use_expenditures',)

            customer = Customer.objects.create(user=u,
                                               id=customer.id,
                                               plan='paid-plan')

            return HttpResponseRedirect('/budget/')
    else:
        return render(request, template_name)

@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def new_user_setup(request):
    u = User.objects.get(username=request.user)

    emp = Employee.objects.get(user=u)
    if request.method == 'GET':
        if not emp.new_user:
            return render(request, 'new_user_setup.html', {'new_user': False})
        else:
            form = NewUserSetupForm()
            return render(request, 'new_user_setup.html', {'new_user': True, 'form': form})

    else:
        form = NewUserSetupForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            emp.init_avg_daily_tips = form_data['init_avg_daily_tips']
            emp.new_user = False
            emp.save()
            return HttpResponseRedirect('/expenses/')

@login_required(login_url='/login/')
@permission_required('tipout.use_tips', login_url='/subscribe/')
def enter_tips(request):
    # if this is a POST request, we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request
        form = EnterTipsForm(request.POST)
        # check whether it's valid
        if form.is_valid():
            tip_data = form.cleaned_data

            tip_owner = User.objects.get(username=request.user)

            t = Tip(amount=tip_data['amount'],
                    date_earned=tip_data['date_earned'],
                    owner=tip_owner)
            t.save()
            return HttpResponseRedirect('/tips/')

    # if a GET (or any other method), we'll create a blank form
    else:
        form = EnterTipsForm()
        return render(request, 'enter_tips.html', {'form': form})

# need to be able to view paychecks by month & year
@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/subscribe/')
@require_http_methods(['GET'])
def paychecks(request):
    u = User.objects.get(username=request.user)

    paychecks = Paycheck.objects.filter(owner=u)
    return render(request, 'paychecks.html', {'paychecks': paychecks})

@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/subscribe/')
def enter_paycheck(request):
    if request.method == 'POST':
        form = EnterPaycheckForm(request.POST)
        if form.is_valid():
            u = User.objects.get(username=request.user)
            paycheck_data = form.cleaned_data
            dupe = Paycheck.objects.filter(
                      owner=u
                   ).filter(
                      date_earned=paycheck_data['date_earned']
                   )
            if dupe:
                return render(request,
                              'enter_paycheck.html',
                              {'error_message': 'Paycheck from that date exists.'})
            else:
                p = Paycheck(owner=u,
                             amount=paycheck_data['amount'],
                             date_earned=paycheck_data['date_earned']
                            )
                p.save()
                return HttpResponseRedirect('/paychecks/')
        else:
            # render template w/ error messages
            pass

    else:
        return render(request,
                      'enter_paycheck.html',
                      {'form': EnterPaycheckForm()}
                     )


@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/subscribe/')
def edit_paycheck(request, *args):
    # split paycheck url into (username, 'paycheck', year, month, day)
    u = User.objects.get(username=request.user)
    paycheck_data_split = args[0].split('-')
    paycheck = Paycheck.objects.get(owner=u,
                                    date_earned__year=paycheck_data_split[2],
                                    date_earned__month=paycheck_data_split[3],
                                    date_earned__day=paycheck_data_split[4])

    if request.method == 'GET':
        form = EditPaycheckForm(initial={'paycheck': paycheck})
        return render(request, 'edit_paycheck.html', {'form': form, 'paycheck': paycheck})

    if request.method == 'POST':
        form = EditPaycheckForm(request.POST)
        if form.is_valid():
            paycheck_data = form.cleaned_data
            #
            ## Don't need to check for dupe, since date isn't editable
            #
            p = Paycheck.objects.get(owner=u, date_earned=paycheck.date_earned)
            p.amount = paycheck_data['amount']
            p.save()
            return HttpResponseRedirect('/paychecks/')
        else:
            # render template w/ error messages
            pass

# May not ever need to delete a paycheck
@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/subscribe/')
def delete_paycheck(request):
    pass

@login_required(login_url='/login/')
@permission_required('use_expenses', login_url='/subscribe/')
def enter_expenses(request):
    '''
    On POST request, get expenses data from form and update db.
    On GET request, show enter_expenses template/form.
    '''
    if request.method == 'POST':
        form = EnterExpenseForm(request.POST)
        if form.is_valid():
            u = User.objects.get(username=request.user)
            expense_data = form.cleaned_data
            dupe = Expense.objects.filter(
                       owner=u
                   ).filter(
                       expense_name=expense_data['expense_name'].lower()
                   )
            if dupe:
                return render(request,
                              'enter_expenses.html',
                              {'form': EnterExpenseForm(),
                               'error_message': 'An expense with that name already exists.'})
            else:
                e = Expense(owner=u,
                            cost=expense_data['cost'],
                            expense_name=expense_data['expense_name'].lower(),
                            frequency=expense_data['frequency']
                           )
                e.save()
                return HttpResponseRedirect('/expenses/')
        else:
            # render template with error messages
            pass
    else:
        form = EnterExpenseForm()
        return render(request, 'enter_expenses.html', {'form': form})

@login_required(login_url='/login/')
@permission_required('use_expenses', login_url='/subscribe/')
@require_http_methods(['GET'])
def expenses(request):
    '''
    Get expenses that belong to current user and pass them to the template.
    '''
    u = User.objects.get(username=request.user)
    expenses = Expense.objects.filter(owner=u)
    return render(request, 'expenses.html', {'expenses': expenses})

@login_required(login_url='/login/')
@permission_required('use_tips', login_url='/subscribe/')
@require_http_methods(['GET'])
def tips(request):
    '''
    To template:
    ALL tips that belong to current user.
    Daily avg. tips based on ALL user's tips.
    '''
    u = User.objects.get(username=request.user)

    tips = Tip.objects.filter(owner=u,
                              date_earned__month=date.today().month).order_by('date_earned')[::-1]
    # tips = Tip.objects.filter(owner=u).order_by('date_earned')[:30]
    tip_values = [ tip.amount for tip in tips ]

    return render(request, 'tips.html', {'avg_daily_tips': avg_daily_tips(tip_values), 'tips': tips})

@login_required(login_url='/login/')
def edit_tip(request, *args):
    pass

@login_required(login_url='/login/')
def delete_tip(request, tip_id, *args):

    if request.method == 'POST':
        u = User.objects.get(username=request.user)
        t = Tip.objects.get(owner=u, pk=tip_id)
        t.delete()
        return HttpResponseRedirect('/tips/')

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def budget(request):
    '''
    Get User from request context, then get tips belonging to that user
    and pass the daily average for past 30 days to template.

    Since budget is first view upon login, check to see if user is 'new'.
    If so, and it has been less than 30 days since signup, calculate tips
    based on init_daily_avg_tips. Otherwise, calculate based on actual tips.
    '''

    '''
    If user is new, send to new-user-setup to set init_avg_daily_tips.
    '''

    # get user, employee
    u = User.objects.get(username=request.user)
    emp = Employee.objects.get(user=u)

    # if user is new, send to new-user-setup
    if emp.new_user:
        return HttpResponseRedirect('/new-user-setup/')

    else:
        # expenses, daily expense cost - assuming every expense is paid monthly
        expenses = Expense.objects.filter(owner=u)
        daily_expense_cost = sum([ exp.cost for exp in expenses ]) / 30

        # expenditures for the day
        expenditures_today_query = Expenditure.objects.filter(owner=u, date=date.today())
        expenditures_today = sum([ exp.cost for exp in expenditures_today_query ])

        # get tips for last 30 days
        # not sure if order_by is ascending or descending
        tips = Tip.objects.filter(owner=u).order_by('date_earned')[:30]
        tip_values = [ tip.amount for tip in tips ]

        # user's paychecks
        paychecks = Paycheck.objects.filter(owner=u)
        # paycheck_amts = [ paycheck.amt for paycheck in paychecks ]
        # daily_avg_from_paycheck = (sum(paycheck_amts) / len(paycheck_amts))

        def pretty_dollar_amount(budget):
            pass

        if (date.today() - emp.signup_date).days <= 30:
            budget = avg_daily_tips_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date) + daily_avg_from_paycheck(paychecks) - daily_expense_cost - expenditures_today

            return render(request, 'budget.html', {'avg_daily_tips': emp.init_avg_daily_tips, 'budget': budget})

        else:
            budget = avg_daily_tips(tip_values) + daily_avg_from_paycheck(paychecks) - daily_expense_cost - expenditures_today

            return render(request, 'budget.html', {'avg_daily_tips': avg_daily_tips(tip_values), 'budget': budget})

@login_required(login_url='/login/')
def enter_expenditure(request):
    '''
    If POST, admit and process form. Otherwise, show blank form.
    '''
    if request.method == 'POST':
        form = EnterExpenditureForm(request.POST)
        if form.is_valid():
            # process form data
            u = User.objects.get(username=request.user)
            exp_data = form.cleaned_data
            dupe = Expenditure.objects.filter(
                       owner=u
                   ).filter(
                       date=date.today()
                   ).filter(
                       note=exp_data['note'].lower()
                   )
            if dupe:
                return render(request,
                              'enter_expenditure.html',
                              {'form': EnterExpenditureForm(initial={'date': date.today()}),
                               'error_message': 'An expenditure with that note already exists.'}
                              )
            else:
                e = Expenditure(owner=u, cost=exp_data['cost'], date=exp_data['date'], note=exp_data['note'].lower())
                e.save()
                return HttpResponseRedirect('/expenditures/')
    else:
        return render(request,
                      'enter_expenditure.html',
                      {'form': EnterExpenditureForm(initial={'date': date.today()})}
                      )

# To edit an expenditure, you'll have to use pk to identify it, since the note and amount could change.
# This would effectively be deleting an expenditure and creating a new one, which might be enough anyway.
#
# @login_required(login_url='/login/')
# def edit_expenditure(request, *args):
#     '''
#     Currently, you can only edit *today's* expenditures, so /expenditures/ only
#     queries for today's and that's all you can edit.
#     '''
#     # exp = args[0].replace('-', ' ')
#
#     u = User.objects.get(username=request.user)
#     es = Expenditure.objects.filter(owner=u).filter(date=date.today())
#
#     e = [ e for e in es if str(e) == args[0] ]
#
#     if request.method == 'POST':
#         form = EditExpenditureForm(request.POST)
#         if form.is_valid():
#             exp_data = form.cleaned_data
#
#
#     else:
#         pass

@login_required(login_url='/login/')
def delete_expenditure(request, *args):
    # exp = args[0].replace('-', ' ')

    if request.method == 'POST':
        u = User.objects.get(username=request.user)
        es = Expenditure.objects.filter(owner=u).filter(date=date.today())
        e = None
        test = None
        for exp in es:
            if strip(exp.get_absolute_url(), '/') == args[0]:
                e = exp
        e.delete()
        return HttpResponseRedirect('/expenditures/')

@login_required(login_url='/login/')
@permission_required('use_expenditures', login_url='/subscribe/')
@require_http_methods(['GET'])
def expenditures(request):
    '''
    Default expenditures page show TODAY'S expenditures.
    '''
    u = User.objects.get(username=request.user)
    exps = Expenditure.objects.filter(owner=u).filter(date=date.today())
    return render(request, 'expenditures.html', {'exps': exps})

@login_required(login_url='/login/')
def edit_expense(request, *args):
    exp_name = args[0].replace('-', ' ')

    u = User.objects.get(username=request.user)
    e = Expense.objects.filter(owner=u).get(expense_name=exp_name)

    if request.method == 'GET':
        form = EditExpenseForm(initial={'cost': e.cost})
        return render(request, 'edit_expense.html', {'form': form, 'expense_name': e.expense_name})

    if request.method == 'POST':
        form = EditExpenseForm(request.POST)
        if form.is_valid():
            exp_data = form.cleaned_data
            ##
            # Need to check for dupe here
            ##
            exp = Expense.objects.get(owner=u, expense_name=e.expense_name)
            exp.cost = exp_data['cost']
            exp.save()
            return HttpResponseRedirect('/expenses/')

@login_required(login_url='/login/')
def delete_expense(request, *args):
    exp_name = args[0].replace('-', ' ')

    if request.method == 'POST':
        u = User.objects.get(username=request.user)
        e = Expense.objects.get(owner=u, expense_name=exp_name)
        e.delete()
        return HttpResponseRedirect('/expenses/')

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenditures_archive(request, *args):
    '''
    Shows a list of years
    '''
    u = User.objects.get(username=request.user)
    all_years = [e.date.year for e in Expenditure.objects.filter(owner=u)]
    years = set(all_years)
    return render(request, 'expenditures_archive.html', {'years': years})

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenditures_year_archive(request, year, *args):
    '''
    Shows a list of months
    '''
    u = User.objects.get(username=request.user)
    # all_months = [e.month_name for e in Expenditure.objects.filter(owner=u)
    #                            if e.date.year == year]
    # months = set(all_months)
    dates = Expenditure.objects.filter(owner=u,
                                       date__year=year).dates('date', 'month')
    months = [date.month for date in dates]
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'months': months})

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenditures_month_archive(request, year, month, *args):
    '''
    Shows a list of days
    '''
    u = User.objects.get(username=request.user)
    dates = Expenditure.objects.filter(owner=u,
                                       date__year=year,
                                       date__month=month).dates('date', 'day')
    days = [date.day for date in dates]
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'month': month,
                                                         'days': days})

@login_required(login_url='/login/')
def expenditures_day_archive(request, year, month, day, *args):
    '''
    Shows a list of expenditures
    '''
    u = User.objects.get(username=request.user)
    exps = Expenditure.objects.filter(owner=u,
                                      date__year=year,
                                      date__month=month,
                                      date__day=day)
    # exps_notes = [date.note for exp in exps]
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'month': month,
                                                         'day': day,
                                                         'exps': exps})

@login_required(login_url='/login/')
def expenditure_detail(request, year, month, day, exp, *args):
    '''
    Shows details about a particular expenditure
    '''
    exp_note = exp.replace('-', ' ')

    u = User.objects.get(username=request.user)
    exp = Expenditure.objects.get(owner=u,
                                  date__year=year,
                                  date__month=month,
                                  date__day=day,
                                  note=exp_note)
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'month': month,
                                                         'day': day,
                                                         'exp': exp})

@login_required(login_url='/login/')
def tips_archive(request, year=None, month=None, day=None, *args):
    '''
    See past tips.

    Render the same template but send different data depending on the
    parameters that are past in.
    '''

    u = User.objects.get(username=request.user)

    if not year:
        all_years = [tip.date_earned.year for tip in Tip.objects.filter(owner=u)]
        years = set(all_years)
        return render(request, 'tips_archive.html', {'years': years})

    elif not month:
        dates = Tip.objects.filter(owner=u,
                                   date_earned__year=year).dates('date_earned', 'month')
        months = [date.month for date in dates]
        return render(request, 'tips_archive.html', {'year': year,
                                                     'months': months})
    elif not day:
        dates = Tip.objects.filter(owner=u,
                                   date_earned__year=year,
                                   date_earned__month=month).dates('date_earned', 'day')
        days = [date.day for date in dates]
        return render(request, 'tips_archive.html', {'year': year,
                                                     'month': month,
                                                     'days': days})
    else:
        tips = Tip.objects.filter(owner=u,
                                  date_earned__year=year,
                                  date_earned__month=month,
                                  date_earned__day=day)
        return render(request, 'tips_archive.html', {'year': year,
                                                     'month': month,
                                                     'day': day,
                                                     'tips': tips})
