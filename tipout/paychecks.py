from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from django.utils.timezone import now, timedelta

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

    recent_paychecks = cache.get('recent_paychecks')
    if not recent_paychecks:
        recent_paychecks = Paycheck.objects.filter(owner=emp, date_earned__gt=now().date()-timedelta(30))
        cache.set('recent_paychecks', recent_paychecks)

    return render(request, 'paychecks.html', {'paychecks': recent_paychecks})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def enter_paycheck(request):
    if request.method == 'POST':
        form = EnterPaycheckForm(request.POST)
        if form.is_valid():
            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)

            paycheck_data = form.cleaned_data

            all_paychecks = cache.get('all_paychecks')
            if not all_paychecks:
                all_paychecks = Paycheck.objects.filter(owner=emp)
                cache.set('all_paychecks', all_paychecks)

            dupe = all_paychecks.filter(date_earned=paycheck_data['date_earned'])
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

                all_paychecks = Paycheck.objects.filter(owner=emp)
                cache.set('all_paychecks', all_paychecks)

                if p.date_earned < now().date():
                    update_budgets(emp, p.date_earned)

                return redirect('/paychecks/')
    else:
        return render(request,
                      'enter_paycheck.html',
                      {'form': EnterPaycheckForm()}
                     )

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def edit_paycheck(request, p, *args):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    # split paycheck url into (email, 'paycheck', year, month, day)
    # paycheck_data_split = args[0].split('-')

    all_paychecks = cache.get('all_paychecks')
    if not all_paychecks:
        all_paychecks = Paycheck.objects.filter(owner=emp)
        cache.set('all_paychecks', all_paychecks)

    paycheck = all_paychecks.get(pk=p)

    if request.method == 'POST':
        form = EditPaycheckForm(request.POST)
        if form.is_valid():
            paycheck_data = form.cleaned_data

            paycheck.amount = paycheck_data['amount']
            paycheck.hours_worked = paycheck_data['hours_worked']
            paycheck.date_earned = paycheck_data['date_earned']
            paycheck.save()

            all_paychecks = Paycheck.objects.filter(owner=emp)
            cache.set('all_paychecks', all_paychecks)

            if paycheck.date_earned < now().date():
                update_budgets(emp, paycheck.date_earned)

            return redirect('/paychecks/')

    else:
        form = EditPaycheckForm(initial={'amount': paycheck.amount,
                                         'hours_worked': paycheck.hours_worked,
                                         'date_earned': paycheck.date_earned
                                        }
                               )
        return render(request, 'edit_paycheck.html', {'form': form, 'paycheck': paycheck})


# May not ever need to delete a paycheck
@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['POST'])
def delete_paycheck(request, p):
    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        all_paychecks = cache.get('all_paychecks')
        if not all_paychecks:
            all_paychecks = Paycheck.objects.filter(owner=emp)
            cache.set('all_paychecks', all_paychecks)

        paycheck_to_delete = all_paychecks.get(pk=p)
        # for exp in es:
        #     if strip(exp.get_absolute_url(), '/') == args[0]:
        #         e = exp

        # need date for budgets update
        paycheck_date = paycheck_to_delete.date_earned
        
        paycheck_to_delete.delete()

        all_paychecks = Paycheck.objects.filter(owner=emp)
        cache.set('all_paychecks', all_paychecks)

        if paycheck_date < now().date():
            update_budgets(emp, paycheck_date)

        return redirect('/paychecks/')
