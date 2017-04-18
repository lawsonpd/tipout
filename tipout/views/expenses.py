from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from tipout.models import Employee, Expense, EnterExpenseForm, EditExpenseForm
from custom_auth.models import TipoutUser

@login_required(login_url='/login/')
@permission_required('use_expenses', login_url='/signup/')
@require_http_methods(['GET'])
def expenses(request):
    '''
    Get expenses that belong to current user and pass them to the template.
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    expenses = Expense.objects.filter(owner=emp)
    return render(request, 'expenses.html', {'expenses': expenses})

@login_required(login_url='/login/')
@permission_required('use_expenses', login_url='/signup/')
def enter_expenses(request):
    '''
    On POST request, get expenses data from form and update db.
    On GET request, show enter_expenses template/form.
    '''
    if request.method == 'POST':
        form = EnterExpenseForm(request.POST)
        if form.is_valid():
            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)

            expense_data = form.cleaned_data
            dupe = Expense.objects.filter(
                       owner=emp
                   ).filter(
                       expense_name=expense_data['expense_name'].lower()
                   )
            if dupe:
                return render(request,
                              'enter_expenses.html',
                              {'form': EnterExpenseForm(),
                               'error_message': 'An expense with that name already exists.'})
            else:
                e = Expense(owner=emp,
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
def edit_expense(request, *args):
    exp_name = args[0].replace('-', ' ')

    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    e = Expense.objects.filter(owner=emp).get(expense_name=exp_name)

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
            exp = Expense.objects.get(owner=emp, expense_name=e.expense_name)
            exp.cost = exp_data['cost']
            exp.save()
            return HttpResponseRedirect('/expenses/')

@login_required(login_url='/login/')
def delete_expense(request, *args):
    exp_name = args[0].replace('-', ' ')

    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        e = Expense.objects.get(owner=emp, expense_name=exp_name)
        e.delete()
        return HttpResponseRedirect('/expenses/')
