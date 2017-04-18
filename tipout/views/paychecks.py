from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from tipout.models import Employee, Paycheck, EnterPaycheckForm, EditPaycheckForm
from custom_auth.models import TipoutUser

# need to be able to view paychecks by month & year
@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/signup/')
@require_http_methods(['GET'])
def paychecks(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    paychecks = Paycheck.objects.filter(owner=emp)
    return render(request, 'paychecks.html', {'paychecks': paychecks})

@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/signup/')
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
                              {'error_message': 'Paycheck from that date exists.'})
            else:
                p = Paycheck(owner=emp,
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
@permission_required('use_paychecks', login_url='/signup/')
def edit_paycheck(request, *args):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    # split paycheck url into (email, 'paycheck', year, month, day)
    paycheck_data_split = args[0].split('-')
    paycheck = Paycheck.objects.get(owner=emp,
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
            p = Paycheck.objects.get(owner=emp, date_earned=paycheck.date_earned)
            p.amount = paycheck_data['amount']
            p.save()
            return HttpResponseRedirect('/paychecks/')
        else:
            # render template w/ error messages
            pass

# May not ever need to delete a paycheck
@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/signup/')
def delete_paycheck(request):
    pass
