from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import EnterTipsForm, EnterExpensesForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from tipout.models import Tip, Expense, Employee
from django.contrib.auth.models import User

from tipout.budget import calc_tips_avg

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
@require_http_methods(["GET"])
def tips_summary(request):
    '''
    Get tips that belong to current user and pass them to the template.
    '''
    tips = Tip.objects.filter(owner_id=request.user.id)
    return render(request, 'tips_summary.html', {'tips': tips})

def user_test(request):
    return HttpResponse(request.user.id)

@login_required(login_url='/login/')
@require_http_methods(["GET"])
def budget(request):
    '''
    Get User from request context, then get tips belonging to that user
    and pass the daily average for past 30 days to template.

    *** Currently this implementation averages ALL tips belonging to user
    and does NOT give average just considering past 30 days.
    '''
    u = User.objects.get(username=request.user)
    tip_obj = Tip.objects.filter(owner=u)[:30]
    tip_values = [ tip.amount for tip in tip_obj ]
    daily_tip_avg = calc_tips_avg(tip_values)
    return render(request, 'budget.html', {'daily_tip_avg': daily_tip_avg})
