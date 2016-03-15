from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import EnterTipsForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from tipout.models import Tip, Expense, Employee, Expenditure, EnterExpenditureForm, EnterExpenseForm, EditExpenseForm, NewUserSetupForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login

from tipout.budget import calc_tips_avg, calc_tips_avg_initial
from datetime import date
# from string import lower

# Create your views here.

def home(request):
    '''
    If user is logged in, redirect to '/budget/'. Else, show basic info and provide
    link to registration.
    '''
    if request.user.is_authenticated():
        return HttpResponseRedirect('/budget/')

    else:
        return render(request, 'home.html')

@require_http_methods(['GET', 'POST'])
def register(request, template_name):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # create new User
            user_data = form.cleaned_data

            # create_user automatically saves entry to db
            user = User.objects.create_user(user_data['username'], password=user_data['password1'])

            # create new Employee
            emp = Employee(user=user, new_user=True, init_avg_daily_tips=0, signup_date=date.today())
            emp.save()

            return HttpResponseRedirect('/login/')
        else:
            return render(request, template_name, {'form': form})
    else:
        form = UserCreationForm()
        return render(request, template_name, {'form': form})

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
def enter_tips(request):
    # if this is a POST request, we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request
        form = EnterTipsForm(request.POST)
        # check whether it's valid
        if form.is_valid():
            tip_data = form.cleaned_data

            tip_owner = User.objects.get(username=request.user)

            t = Tip(amount=tip_data['tips_amount'],
                    date_earned=tip_data['date_earned'],
                    owner=tip_owner)
            t.save()
            return HttpResponseRedirect('/tips/')

    # if a GET (or any other method), we'll create a blank form
    else:
        form = EnterTipsForm()

    return render(request, 'enter_tips.html', {'form': form})

@login_required(login_url='/login/')
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
            e = Expense(owner=u,
                        cost=expense_data['cost'],
                        expense_name=expense_data['expense_name'].lower(),
                        frequency=expense_data['frequency'])
            e.save()

            return HttpResponseRedirect('/expenses/')
    else:

        form = EnterExpenseForm()
        return render(request, 'enter_expenses.html', {'form': form})

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenses(request):
    '''
    Get expenses that belong to current user and pass them to the template.
    '''
    u = User.objects.get(username=request.user)
    expenses = Expense.objects.filter(owner=u)
    return render(request, 'expenses.html', {'expenses': expenses})

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def tips(request):
    '''
    Get tips that belong to current user and pass them to the template.
    '''
    tips = Tip.objects.filter(owner_id=request.user.id)
    return render(request, 'tips.html', {'tips': tips})

def user_test(request):
    return HttpResponse(request.user.id)

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

    if (date.today() - emp.signup_date).days <= 30:
        budget = calc_tips_avg_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date) - daily_expense_cost - expenditures_today

        return render(request, 'budget.html', {'avg_daily_tips': emp.init_avg_daily_tips, 'budget': budget})

    else:
        avg_daily_tips = calc_tips_avg(tips_value)
        budget = avg_daily_tips - daily_expense_cost - expenditures_today

        return render(request, 'budget.html', {'avg_daily_tips': avg_daily_tips, 'budget': budget})

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
            e = Expenditure(owner=u, cost=exp_data['cost'], date=exp_data['date'], note=exp_data['note'].lower())
            e.save()

            return HttpResponseRedirect('/budget/')
    else:
        form = EnterExpenditureForm(initial={'date': date.today()})

    return render(request, 'enter_expenditure.html', {'form': form})

@login_required(login_url='/login/')
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
def expenditures_month_archive(request, *args):
    pass

@login_required(login_url='/login/')
def expenditures_day_archive(request, *args):
    pass

@login_required(login_url='/login/')
def expenditures_year_archive(request, *args):
    pass

@login_required(login_url='/login/')
def expenditure_detail(request, *args):
    pass
