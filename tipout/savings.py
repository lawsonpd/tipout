from tipout.models import Savings, SavingsTransactions, Employee

from custom_auth.models import TipoutUser

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now, timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_control

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET'])
def savings(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    savings = Savings.objects.get(owner=u)

    return render(request, 'savings.html', {'savings': savings})

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def savings_setup(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    savings = Savings.objects.get(owner=u)

    if request.method == 'POST':
    	pass

    else:
    	return render(request, 'savings_setup.html')

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def deposit_to_savings(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    savings = Savings.objects.get(owner=u)

@cache_control(private=True)
@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def withdraw_from_savings(request):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    savings = Savings.objects.get(owner=u)

