from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control

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

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
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

@cache_control(private=True)
@login_required(login_url='/login/')
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

        tips = cache.get('tips')
        if not tips:
            tips = Tip.objects.filter(owner=emp)
            cache.set('tips', tips)

        # tips = Tip.objects.filter(owner=emp,
        #                           date_earned__month=now().date().month).order_by('date_earned')[::-1]
        if (now().date() - emp.signup_date).days <= 30:
            tip_values = [ tip.amount for tip in tips ]
            avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date))
            return render(request, 'tips.html', {'avg_daily_tips': avg_daily_tips,
                                                 'tips': tips,
                                                 'month': t.strftime('%B')
                                                }
                         )
        else:
            recent_tips = tips.filter(date_earned__gt=(now().date()-timedelta(30)))
            tip_values = [ tip.amount for tip in recent_tips ]
            avg_daily_tips = pretty_dollar_amount(avg_daily_tips_earned(tip_values))
            return render(request, 'tips.html', {'avg_daily_tips': avg_daily_tips,
                                                 'tips': tips,
                                                 'month': t.strftime('%B')
                                                }
                         )

@cache_control(private=True)
@login_required(login_url='/login/')
def edit_tip(request, *args):
    pass

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['POST'])
def delete_tip(request, tip_id, *args):

    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        tips = cache.get('tips')
        if not tips:
            tips = Tip.objects.filter(owner=emp)
            cache.set('tips', tips)

        t = tips.get(owner=emp, pk=tip_id)
        t.delete()

        tips = Tip.objects.filter(owner=emp)
        cache.set('tips', tips)

        if t.date_earned < now().date():
            update_budgets(emp, t.date_earned)

        return redirect('/tips/')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def tips_archive(request, year=None, month=None, day=None, *args):
    '''
    See past tips.

    Render the same template but send different data depending on the
    parameters that are past in.
    '''

    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    tips = cache.get('tips')
    if not tips:
        tips = Tip.objects.filter(owner=emp)
        cache.set('tips', tips)

    if not year:
        all_years = [tip.date_earned.year for tip in tips]
        years = set(all_years)
        return render(request, 'tips_archive.html', {'years': years})

    elif not month:
        dates = tips.filter(date_earned__year=year).dates('date_earned', 'month')
        months = [date.month for date in dates]
        return render(request, 'tips_archive.html', {'year': year,
                                                     'months': months})
    elif not day:
        dates = tips.filter(date_earned__year=year,
                            date_earned__month=month).dates('date_earned', 'day')
        days = [date.day for date in dates]
        return render(request, 'tips_archive.html', {'year': year,
                                                     'month': month,
                                                     'days': days})
    else:
        tips_for_day = tips.filter(date_earned__year=year,
                                   date_earned__month=month,
                                   date_earned__day=day)
        return render(request, 'tips_archive.html', {'year': year,
                                                     'month': month,
                                                     'day': day,
                                                     'tips': tips_for_day})
