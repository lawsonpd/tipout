from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import login, logout
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.views.decorators.cache import cache_control

from custom_auth.models import TipoutUser
from django.core.mail import send_mail
from django.utils.timezone import now

from tipout_demo.models import Tip, DemoEmployee, NewUserSetupForm, Budget, Feedback
from tipout_demo.budget_with_balance import update_budgets
# from django.conf import settings

from budgettool.settings import CACHE_HASH_KEY
from hashlib import md5
import hmac

@require_http_methods(['GET'])
def home(request, template_name):
    '''
    If user is logged in, redirect to '/budget/', else send to home page.
    '''
    # using 'has_module_perms' since for some reason
    # django was seeing anonymous user as an authenticated user and
    # was redirecting to budget, which then redirected to signup page
    if request.user.has_module_perms('tipout'):
        return redirect('/demo/budget/')
    else:
        return render(request, template_name)

@require_http_methods(['GET', 'POST'])
def feedback(request):
    if request.method == 'GET':
        return render(request, 'demo-feedback.html')
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
        return redirect('/demo/thankyou/')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def new_user_setup(request):
    u = TipoutUser.objects.get(email=request.user)
    # demo_alive = request.session.get('demo_alive', False)

    # if not demo_alive:
    #     u.delete()
    #     return render(request, 'home.html')

    emp = DemoEmployee.objects.get(user=u)
    emp_cache_key = hmac.new(CACHE_HASH_KEY, emp.user.email.encode('utf-8'), md5).hexdigest()

    if request.method == 'GET':
        if not emp.new_user:
            return render(request, 'demo-new_user_setup.html', {'new_user': False})
        else:
            form = NewUserSetupForm()
            return render(request, 'demo-new_user_setup.html', {'new_user': True, 'form': form})

    elif request.method == 'POST':
        form = NewUserSetupForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            emp.init_avg_daily_tips = form_data['init_avg_daily_tips']
            emp.new_user = False
            emp.save()

            # update all budgets since emp signed up
            update_budgets(emp, emp.signup_date)

            return redirect('/demo/other-funds/')

# @require_http_methods(['GET'])
# def how_it_works(request):
#     if request.method == 'GET':
#         return render(request, 'how_it_works.html')

@require_http_methods(['GET'])
def faq(request):
    if request.method == 'GET':
        return render(request, 'demo-faq.html')

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def view_feedback(request):
    u = TipoutUser.objects.get(email=request.user)

    if u.is_staff:
        all_feedback = Feedback.objects.all().order_by('-date')
        return render(request, 'view_feedback.html', {'feedback': all_feedback})
    else:
        return render(request, 'demo-404.html')

@require_http_methods(['GET'])
def add_to_homescreen(request):
    if request.method == 'GET':
        return render(request, 'demo-add_to_homescreen.html')
