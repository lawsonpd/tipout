from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now

from tipout.models import Tip, EnterTipsForm, Employee
from custom_auth.models import TipoutUser
from budget_utils import (avg_daily_tips_earned,
                          avg_daily_tips_earned_initial,
                          tips_available_per_day_initial,
                          tips_available_per_day,
                          daily_avg_from_paycheck,
                          pretty_dollar_amount,
                          update_budgets
                         )

@login_required(login_url='/login/')
@permission_required('tipout.use_tips', login_url='/signup/')
def enter_tips(request):
    # if this is a POST request, we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request
        form = EnterTipsForm(request.POST)
        # check whether it's valid
        if form.is_valid():
            tip_data = form.cleaned_data

            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)

            t = Tip(amount=tip_data['amount'],
                    date_earned=tip_data['date_earned'],
                    owner=emp)
            t.save()
            if t.date_earned < now().date():
                update_budgets(emp, t.date_earned)
            return redirect('/tips/')

    # if a GET (or any other method), we'll create a blank form
    else:
        form = EnterTipsForm()
        return render(request, 'enter_tips.html', {'form': form})

@login_required(login_url='/login/')
@permission_required('use_tips', login_url='/signup/')
@require_http_methods(['GET'])
def tips(request):
    '''
    To template:
    ALL tips that belong to current user.
    Daily avg. tips based on ALL user's tips.
    '''
    if request.method == 'GET':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)
        t = now().date()
        # tips = Tip.objects.filter(owner=emp,
        #                           date_earned__month=now().date().month).order_by('date_earned')[::-1]
        if (now().date() - emp.signup_date).days <= 30:
            tips = Tip.objects.filter(owner=emp).order_by('-date_earned')
            tip_values = [ tip.amount for tip in tips ]
            avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date))
            return render(request, 'tips.html', {'avg_daily_tips': avg_daily_tips,
                                                 'tips': tips,
                                                 'month': t.strftime('%B')
                                                }
                         )
        else:
            tips = Tip.objects.filter(owner=emp,
                                      date_earned__month=now().date().month).order_by('-date_earned')
            tip_values = [ tip.amount for tip in tips ]
            avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned(tip_values))
            return render(request, 'tips.html', {'avg_daily_tips': avg_daily_tips,
                                                 'tips': tips,
                                                 'month': t.strftime('%B')
                                                }
                         )

@login_required(login_url='/login/')
def edit_tip(request, *args):
    pass

@login_required(login_url='/login/')
def delete_tip(request, tip_id, *args):

    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        t = Tip.objects.get(owner=emp, pk=tip_id)
        t.delete()
        if t.date_earned < now().date():
            update_budgets(emp, t.date_earned)
        return redirect('/tips/')

@login_required(login_url='/login/')
def tips_archive(request, year=None, month=None, day=None, *args):
    '''
    See past tips.

    Render the same template but send different data depending on the
    parameters that are past in.
    '''

    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    if not year:
        all_years = [tip.date_earned.year for tip in Tip.objects.filter(owner=emp)]
        years = set(all_years)
        return render(request, 'tips_archive.html', {'years': years})

    elif not month:
        dates = Tip.objects.filter(owner=emp,
                                   date_earned__year=year).dates('date_earned', 'month')
        months = [date.month for date in dates]
        return render(request, 'tips_archive.html', {'year': year,
                                                     'months': months})
    elif not day:
        dates = Tip.objects.filter(owner=emp,
                                   date_earned__year=year,
                                   date_earned__month=month).dates('date_earned', 'day')
        days = [date.day for date in dates]
        return render(request, 'tips_archive.html', {'year': year,
                                                     'month': month,
                                                     'days': days})
    else:
        tips = Tip.objects.filter(owner=emp,
                                  date_earned__year=year,
                                  date_earned__month=month,
                                  date_earned__day=day)
        return render(request, 'tips_archive.html', {'year': year,
                                                     'month': month,
                                                     'day': day,
                                                     'tips': tips})
