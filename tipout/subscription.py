from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from custom_auth.admin import UserCreationForm
from custom_auth.models import TipoutUser
from tipout.models import Employee, Budget, Balance, Savings
from tipout.stripe_utils import pretty_date, pretty_stripe_dollar_amount, refund_approved, most_recent_invoice
import stripe

from budgettool.settings import STRIPE_KEYS
stripe.api_key = STRIPE_KEYS['secret_key']

@require_http_methods(['GET', 'POST'])
def register(request, template_name):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user_data = form.cleaned_data

            # if user_data['email'] != request.POST['stripeEmail']:
            #     raise forms.ValidationError('Email fields must match.')
            # else:
            #     return HttpResponse(user_data['email'])

            # user = TipoutUser.objects.create_user(email=user_data['email'],
            #                                       password=user_data['password1'])
            #
            # u = TipoutUser.objects.get(email=request.user)
            #
            # subs = Group.objects.get(name='subscribers')
            # user.groups.add(subs)
            #
            # return HttpResponse(u.has_perm('tipout.use_tips'))
            # emp = Employee.objects.create(user=user,
            #                               new_user=True,
            #                               init_avg_daily_tips=0,
            #                               signup_date=date.today())

            # return redirect('/login/')
        # RESPONSE: email
        #           password1
        #           password2
        #           stripeEmail
        #           stripeToken
        #           stripeTokenType
        #           csrfmiddlewaretoken
        # else:
        #     return render(request, template_name, {'form': form})
            # create new Employee
            # emp = Employee.objects.create(user=user,
            #                               new_user=True,
            #                               init_avg_daily_tips=0)
            #
            # return redirect('/login/')
        else:
            return render(request, template_name, {'form': form})
    else:
        form = UserCreationForm()
        return render(request, template_name, {'form': form})

@require_http_methods(['GET', 'POST'])
def signup(request, template_name):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user_data = form.cleaned_data

            try:
                customer = stripe.Customer.create(
                    email = request.POST['stripeEmail'],
                    source = request.POST['stripeToken'],
                    plan='paid-plan',
                    coupon=user_data['coupon'],
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
                                                      coupon=user_data['coupon'],
                                                      password=user_data['password1'],
                                                      city=user_data['city'],
                                                      state=user_data['state']
            )

            new_emp = Employee.objects.create(user=new_user)
            emp_first_budget = Budget.objects.create(owner=new_emp, amount=0)
            emp_balance = Balance.objects.create(owner=new_emp)
            emp_savings = Savings.objects.create(owner=new_emp, default=0)

            # coupon to pass to 'thankyou' template
            stripe_coupon = new_user.coupon

            user = authenticate(email=user_data['email'], password=user_data['password1'])
            if user is not None:
                login(request, user)
                return redirect('/thankyou/')
            else:
                return render (request, 'registration/signup_error.html', {'message': "Something went wrong. Registration unsuccessful."})

    else:
        form = UserCreationForm()
    return render(request, template_name, {'form': form, 'key': STRIPE_KEYS['publishable_key']})

@require_http_methods(['GET'])
def thank_you(request):
    if request.user.has_module_perms('tipout'):
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)
        if emp.new_user:
            return render(request, 'registration/charge.html', {'amount': '5.00', 'coupon': u.coupon})
        else:
            return render(request, 'thankyou.html')
    return render(request, 'thankyou.html')

@login_required(login_url='/login/')
@require_http_methods(['GET'])
def manage_subscription(request):
    u = TipoutUser.objects.get(email=request.user)
    customer = stripe.Customer.retrieve(u.stripe_id)
    # sub_id = customer.subscriptions.data[0].id
    # invoices = stripe.Invoice.list(customer) # this doesn't seem to work
    invoices = stripe.Invoice.list()

    customer_invoices = filter(lambda invoice: invoice.customer == customer.id, invoices)
    invoice_data = [(pretty_date(invoice.date), pretty_stripe_dollar_amount(invoice.amount_due)) for invoice in customer_invoices]

    return render(request, 'registration/subscription.html', {'invoice_data': invoice_data})

@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def cancel_subscription(request):
    if request.method == 'GET':
        return render(request, 'registration/cancel.html')
    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        u.delete()

        customer = stripe.Customer.retrieve(u.stripe_id)
        sub = stripe.Subscription.retrieve(customer.subscriptions.data[0].id)
        sub.delete()

        customer_next_invoice = stripe.Invoice.upcoming(customer=customer.id)
        if refund_approved(customer_next_invoice.date):
            customer_invoices = filter(lambda invoice: invoice.customer == customer.id, invoices)
            invoice_to_refund = most_recent_invoice(customer_invoices)
            re = stripe.Refund.create(charge=invoice_to_refund.charge)

        # redirect to feedback page
        return redirect('/feedback/')
