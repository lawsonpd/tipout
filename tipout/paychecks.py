from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.views.decorators.cache import cache_control

from tipout.models import Employee, Paycheck, EnterPaycheckForm, EditPaycheckForm
from tipout.budget_utils import update_budgets
from custom_auth.models import TipoutUser

# need to be able to view paychecks by month & year
@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def paychecks(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    paychecks = Paycheck.objects.filter(owner=emp)
    return render(request, 'paychecks.html', {'paychecks': paychecks})

@login_required(login_url='/login/')
def enter_paycheck(request):
    if request.method == 'POST':
        form = EnterPaycheckForm(request.POST)
        if form.is_valid():
            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)

            paycheck_data = form.cleaned_data
            dupe = Paycheck.objects.filter(
                      owner=emp
                   ).filter(
                      date_earned=paycheck_data['date_earned']
                   )
            if dupe:
                return render(request,
                              'enter_paycheck.html',
                              {'error_message': 'Paycheck from that date exists.',
                               'form': EnterPaycheckForm()})
            else:
                p = Paycheck(owner=emp,
                             amount=paycheck_data['amount'],
                             date_earned=paycheck_data['date_earned'],
                             hours_worked=paycheck_data['hours_worked'],
                            )
                p.save()
                if p.date_earned < now().date():
                    update_budgets(emp, p.date_earned)
                return redirect('/paychecks/')
    else:
        return render(request,
                      'enter_paycheck.html',
                      {'form': EnterPaycheckForm()}
                     )


@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def edit_paycheck(request, p, *args):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    # split paycheck url into (email, 'paycheck', year, month, day)
    # paycheck_data_split = args[0].split('-')
    paycheck = Paycheck.objects.get(owner=emp, pk=p)

    if request.method == 'GET':
        form = EditPaycheckForm(initial={'amount': paycheck.amount,
                                         'hours_worked': paycheck.hours_worked,
                                         'date_earned': paycheck.date_earned
                                        }
                               )
        return render(request, 'edit_paycheck.html', {'form': form, 'paycheck': paycheck})

    if request.method == 'POST':
        form = EditPaycheckForm(request.POST)
        if form.is_valid():
            paycheck_data = form.cleaned_data

            paycheck.amount = paycheck_data['amount']
            paycheck.hours_worked = paycheck_data['hours_worked']
            paycheck.date_earned = paycheck_data['date_earned']
            paycheck.save()
            if paycheck.date_earned < now().date():
                update_budgets(emp, paycheck.date_earned)
            return redirect('/paychecks/')

# May not ever need to delete a paycheck
@login_required(login_url='/login/')
@require_http_methods(['POST'])
def delete_paycheck(request, p):
    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        paycheck_to_delete = Paycheck.objects.get(owner=emp, pk=p)
        # for exp in es:
        #     if strip(exp.get_absolute_url(), '/') == args[0]:
        #         e = exp
        paycheck_to_delete.delete()
        if paycheck_to_delete.date_earned < now().date():
            update_budgets(emp, paycheck_to_delete.date_earned)
        return redirect('/paychecks/')
