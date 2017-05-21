from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from custom_auth.admin import UserCreationForm
from custom_auth.models import TipoutUser
from tipout.models import Employee, Budget, Balance
from stripe_utils import pretty_date, pretty_stripe_dollar_amount, refund_approved, most_recent_invoice
import stripe

from budgettool.test_settings import STRIPE_KEYS
# stripe.api_key=STRIPE_KEYS['test_sk']

@require_http_methods(['GET', 'POST'])
def signup_test(request, template_name):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user_data = form.cleaned_data

            try:
                customer = stripe.Customer.create(
                    email = request.POST['stripeEmail'],
                    source = request.POST['stripeToken'],
                    plan='paid-plan',
                )
            except stripe.error.CardError as e:
                return render('registration/signup_error.html', {'message': e['message']})
            except stripe.error.RateLimitError as e:
                return render('registration/signup_error.html', {'message': e['message']})
            except stripe.error.InvalidRequestError as e:
                return render('registration/signup_error.html', {'message': e['message']})
            except stripe.error.APIConnectionError as e:
                return render('registration/signup_error.html', {'message': e['message']})
            except stripe.error.StripeError as e:
                # maybe also send an email to admin@
                return render('registration/signup_error.html', {'message': e['message']})
            except Exception as e:
                return render('registration/signup_error.html', {'message': "We're not exactly sure what happened, but you're welcome to try signing up again."})

            new_user = TipoutUser.objects.create_user(email=user_data['email'],
                                                      stripe_email=customer.email,
                                                      stripe_id=customer.id,
                                                      password=user_data['password1'],
                                                      city=user_data['city'],
                                                      state=user_data['state']
            )

            new_emp = Employee.objects.create(user=new_user)
            emp_first_budget = Budget.objects.create(owner=new_emp, amount=0)
            emp_balance = Balance.objects.create(owner=new_emp)

            user = authenticate(email=user_data['email'], password=user_data['password1'])
            if user is not None:
                login(request, user)

            return redirect('/thankyou/')

    else:
        form = UserCreationForm()
    return render(request, template_name, {'form': form, 'key': STRIPE_KEYS['test_pk']})
