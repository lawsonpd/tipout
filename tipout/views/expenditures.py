from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from tipout.models import Employee, Expenditure, EnterExpenditureForm
from custom_auth.models import TipoutUser

@login_required(login_url='/login/')
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
            dupe = Expenditure.objects.filter(
                       owner=emp
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
                e = Expenditure(owner=emp, cost=exp_data['cost'], date=exp_data['date'], note=exp_data['note'].lower())
                e.save()
                return HttpResponseRedirect('/expenditures/')
    else:
        return render(request,
                      'enter_expenditure.html',
                      {'form': EnterExpenditureForm(initial={'date': date.today()})}
                      )

@login_required(login_url='/login/')
@permission_required('use_expenditures', login_url='/signup/')
@require_http_methods(['GET'])
def expenditures(request):
    '''
    Default expenditures page show TODAY'S expenditures.
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    exps = Expenditure.objects.filter(owner=emp).filter(date=date.today())
    return render(request, 'expenditures.html', {'exps': exps})

@login_required(login_url='/login/')
def delete_expenditure(request, *args):
    # exp = args[0].replace('-', ' ')

    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        es = Expenditure.objects.filter(owner=emp).filter(date=date.today())
        e = None
        test = None
        for exp in es:
            if strip(exp.get_absolute_url(), '/') == args[0]:
                e = exp
        e.delete()
        return HttpResponseRedirect('/expenditures/')

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
#     u = TipoutUser.objects.get(email=request.user)
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
@require_http_methods(['GET'])
def expenditures_archive(request, *args):
    '''
    Shows a list of years
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    all_years = [e.date.year for e in Expenditure.objects.filter(owner=emp)]
    years = set(all_years)
    return render(request, 'expenditures_archive.html', {'years': years})

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def expenditures_year_archive(request, year, *args):
    '''
    Shows a list of months
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    # all_months = [e.month_name for e in Expenditure.objects.filter(owner=u)
    #                            if e.date.year == year]
    # months = set(all_months)
    dates = Expenditure.objects.filter(owner=emp,
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
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    dates = Expenditure.objects.filter(owner=emp,
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
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    exps = Expenditure.objects.filter(owner=emp,
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

    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    exp = Expenditure.objects.get(owner=emp,
                                  date__year=year,
                                  date__month=month,
                                  date__day=day,
                                  note=exp_note)
    return render(request, 'expenditures_archive.html', {'year': year,
                                                         'month': month,
                                                         'day': day,
                                                         'exp': exp})
