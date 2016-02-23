from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import EnterTipsForm, EnterExpensesForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from tipout.models import Tip, Expense, Employee, Expenditure, EnterExpenditureForm
from django.contrib.auth.models import User

from tipout.budget import calc_tips_avg, calc_tips_avg_initial
from datetime import date

# Create your views here.

def index(request):
    '''
    Dummy response
    '''
    return HttpResponse("hello world")

@login_required(login_url='/login/')
def enter_tips(request):
    # if this is a POST request, we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request
        form = EnterTipsForm(request.POST)
        # check whether it's valid
        if form.is_valid():
            tip_data = form.cleaned_data

            tip_owner = User.objects.get(pk=request.user.id)

            t = Tip(amount=tip_data['tips_amount'],
                    date_earned=tip_data['date_earned'],
                    owner=tip_owner)
            t.save()
            return HttpResponseRedirect('/summary/')

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
        form = EnterExpensesForm(request.POST)
        if form.is_valid():
            expense_data = form.cleaned_data
            tip_owner = User.objects.get(pk=request.user.id)
            e = Expense(cost=expense_data['cost'],
                        expense_name=expense_data['expense_name'],
                        frequency=expense_data['frequency'],
                        owner=tip_owner)
            e.save()
            return HttpResponseRedirect('/expenses/')
    else:
        form = EnterExpensesForm()

    return render(request, 'enter_expenses.html', {'form': form})

@login_required(login_url='/login/')
@require_http_methods(["GET"])
def view_expenses(request):
    '''
    Get expenses that belong to current user and pass them to the template.
    '''
    expenses = Expense.objects.filter(owner_id=request.user.id)
    return render(request, 'view_expenses.html', {'expenses': expenses})

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def tips_summary(request):
    '''
    Get tips that belong to current user and pass them to the template.
    '''
    tips = Tip.objects.filter(owner_id=request.user.id)
    return render(request, 'tips_summary.html', {'tips': tips})

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

    # get user, employee
    u = User.objects.get(username=request.user)
    emp = Employee.objects.get(user=u)

    # expenses, daily expense cost - assuming every expense is paid monthly
    exps = Expense.objects.filter(owner=u)
    daily_expense_cost = sum([ exp.cost for exp in exps ]) / 30

    # get tips for last 30 days
    # not sure if order_by is ascending or descending
    tips = Tip.objects.filter(owner=u).order_by('date_earned')[:30]
    tip_values = [ tip.amount for tip in tips ]

    if (date.today() - emp.signup_date).days < 30:
        budget = calc_tips_avg_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date) - daily_expense_cost

        return render(request, 'budget.html', {'avg_daily_tips': emp.init_avg_daily_tips, 'budget': budget})

    else:
        # if user signed up more than 30 days ago, flip new_user flag
        emp.new_user = False
        avg_daily_tips = calc_tips_avg(tips_value)
        budget = avg_daily_tips - daily_expense_cost

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
            e = Expenditure(owner=u, cost=exp_data['cost'], date=exp_data['date'])
            e.save()

            return HttpResponseRedirect('/summary/')
    else:
        form = EnterExpenditureForm(initial={'date': date.today()})

    return render(request, 'enter_expenditure.html', {'form': form})

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def view_expenditures(request):
    u = User.objects.get(username=request.user)
    exps = Expenditure.objects.filter(owner=u).filter(date=date.today())
    return render(request, 'expenditures.html', {'exps': exps})
