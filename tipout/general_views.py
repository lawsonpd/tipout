from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods

from tipout.models import Tip, Employee, NewUserSetupForm, Budget
from custom_auth.models import TipoutUser
from django.core.mail import send_mail
from django.utils.timezone import now
# from django.conf import settings

@require_http_methods(['GET'])
def home(request, template_name):
    '''
    If user is logged in, redirect to '/budget/', else send to home page.
    '''
    # using 'has_module_perms' since for some reason
    # django was seeing anonymous user as an authenticated user and
    # was redirecting to budget, which then redirected to signup page
    if request.user.has_module_perms('tipout'):
        return redirect('/budget/')
    else:
        return render(request, template_name)

@require_http_methods(['GET', 'POST'])
def feedback(request):
    if request.method == 'GET':
        return render(request, 'feedback.html')
    if request.method == 'POST':
        # could use request.META['HTTP_REFERER'] to get referring page
        # form_data = form.cleaned_data
        # send_mail(
        #     'Feedback',
        #     request.POST['feedback'],
        #     request.POST['email'],
        #     ['support@tipoutapp.com'],
        #     fail_silently=True,
        # )
        Feedback.objects.create(
            email=request.POST['email'],
            feedback=request.POST['feedback'],
            refer_likelihood=request.POST['inlineRadioOptions']
        )
        return redirect('/thankyou/')

@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def new_user_setup(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    if request.method == 'GET':
        if not emp.new_user:
            return render(request, 'new_user_setup.html', {'new_user': False})
        else:
            form = NewUserSetupForm()
            return render(request, 'new_user_setup.html', {'new_user': True, 'form': form})

    else:
        form = NewUserSetupForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            emp.init_avg_daily_tips = form_data['init_avg_daily_tips']
            emp.new_user = False
            emp.save()
            b = Budget.objects.create(owner=emp,
                                      date=now().date(),
                                      amount=today_budget())
            return redirect('/expenses/')

# @require_http_methods(['GET'])
# def how_it_works(request):
#     if request.method == 'GET':
#         return render(request, 'how_it_works.html')

@require_http_methods(['GET'])
def faq(request):
    if request.method == 'GET':
        return render(request, 'faq.html')
