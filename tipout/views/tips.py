from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from tipout.models import Tip, EnterTipsForm, Employee
from custom_auth.models import TipoutUser

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
            return HttpResponseRedirect('/tips/')

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
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    tips = Tip.objects.filter(owner=emp,
                              date_earned__month=date.today().month).order_by('date_earned')[::-1]
    # tips = Tip.objects.filter(owner=u).order_by('date_earned')[:30]
    tip_values = [ tip.amount for tip in tips ]

    return render(request, 'tips.html', {'avg_daily_tips': avg_daily_tips(tip_values), 'tips': tips})

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
        return HttpResponseRedirect('/tips/')

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
