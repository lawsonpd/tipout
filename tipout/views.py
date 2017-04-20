from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from tipout.models import Tip, EnterTipsForm, Paycheck, EditPaycheckForm, Expense, Employee, Expenditure, EnterPaycheckForm, EnterExpenditureForm, EnterExpenseForm, EditExpenseForm, NewUserSetupForm
from django.contrib.auth.models import Group
# from django.contrib.auth.forms import UserCreationForm
from custom_auth.admin import UserCreationForm
from custom_auth.models import TipoutUser
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required

from django.views.generic.edit import DeleteView

from tipout.budget import avg_daily_tips, avg_daily_tips_initial, daily_avg_from_paycheck
from datetime import date
from django.utils.timezone import now
# whatever is using strip should be moved into utils
from string import strip
# from string import lower

from budgettool.settings import STRIPE_KEYS
from django.conf import settings

from stripe_utils import pretty_date, pretty_dollar_amount, refund_approved, most_recent_invoice

import stripe
stripe.api_key = settings.STRIPE_KEYS['secret_key']

from django.core.mail import send_mail

import logging
logger = logging.getLogger(__name__)

@require_http_methods(['GET'])
def home(request, template_name):
    '''
    If user is logged in, redirect to '/budget/', else send to home page.
    '''
    if request.user.has_module_perms('tipout'):
        return redirect('/budget/')
    else:
        return render(request, template_name)

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
            #                               signup_date=now().date()

            # return HttpResponseRedirect('/login/')
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
            # return HttpResponseRedirect('/login/')
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
                )
            except stripe.error.CardError as e:
                body = e.json_body
                err = body['error']
                logger.error("Type is: %s; Param is %s" % (err['type'], err['param']))
                return render('registration/signup_error.html', {'message': err['message']})
            except stripe.error.RateLimitError as e:
                body = e.json_body
                err = body['error']
                logger.error("Type is: %s; Param is %s" % (err['type'], err['param']))
                return render('registration/signup_error.html', {'message': err['message']})
            except stripe.error.InvalidRequestError as e:
                body = e.json_body
                err = body['error']
                logger.error("Type is: %s; Param is %s" % (err['type'], err['param']))
                return render('registration/signup_error.html', {'message': err['message']})
            except stripe.error.APIConnectionError as e:
                body = e.json_body
                err = body['error']
                logger.error("Type is: %s; Param is %s" % (err['type'], err['param']))
                return render('registration/signup_error.html', {'message': err['message']})
            except stripe.error.StripeError as e:
                # maybe also send an email to admin@
                body = e.json_body
                err = body['error']
                logger.error("Type is: %s; Param is %s" % (err['type'], err['param']))
                return render('registration/signup_error.html', {'message': err['message']})
            except Exception as e:
                body = e.json_body
                err = body['error']
                logger.error("Type is: %s; Param is %s" % (err['type'], err['param']))
                return render('registration/signup_error.html', {'message': "We're not exactly sure what happened, but you're welcome to try signing up again."})

            new_user = TipoutUser.objects.create_user(email=user_data['email'],
                                                      stripe_email=customer.email,
                                                      stripe_id=customer.id,
                                                      password=user_data['password1'],
                                                      city=user_data['city'],
                                                      state=user_data['state']
            )

            Employee.objects.create(user=new_user)

            user = authenticate(email=user_data['email'], password=user_data['password1'])
            if user is not None:
                login(request, user)

            return redirect('/thankyou/')

    else:
        form = UserCreationForm()
    return render(request, template_name, {'form': form, 'key': STRIPE_KEYS['publishable_key']})

@require_http_methods(['GET'])
def thank_you(request):
    if request.user.has_module_perms('tipout'):
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)
        if emp.new_user:
            return render(request, 'registration/charge.html', {'amount': '5.00'})
    else:
        return render(request, 'thankyou.html')

@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def subscription(request):
    u = TipoutUser.objects.get(email=request.user)
    customer = stripe.Customer.retrieve(u.stripe_id)
    # sub_id = customer.subscriptions.data[0].id
    # invoices = stripe.Invoice.list(customer) # this doesn't seem to work
    invoices = stripe.Invoice.list()

    customer_invoices = filter(lambda invoice: invoice.customer == customer.id, invoices)
    invoice_data = [(pretty_date(invoice.date), pretty_dollar_amount(invoice.amount_due)) for invoice in customer_invoices]

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

@require_http_methods(['GET', 'POST'])
def feedback(request):
    if request.method == 'GET':
        return render(request, 'feedback.html')
    if request.method == 'POST':
        # could use request.META['HTTP_REFERER'] to get referring page
        # form_data = form.cleaned_data
        send_mail(
            'Feedback',
            request.POST['feedback'],
            request.POST['email'],
            ['support@tipoutapp.com'],
            fail_silently=True,
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
            return HttpResponseRedirect('/expenses/')

@login_required(login_url='/login/')
@permission_required('tipout.use_tips', login_url='/signup/')
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
                    owner=emp,
                    hours_worked=tip_data['hours_worked'])
            t.save()
            return HttpResponseRedirect('/tips/')

    # if a GET (or any other method), we'll create a blank form
    else:
        form = EnterTipsForm()
        return render(request, 'enter_tips.html', {'form': form})

# need to be able to view paychecks by month & year
@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/signup/')
@require_http_methods(['GET'])
def paychecks(request):
    if request.method == 'GET':
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
                             date_earned=paycheck_data['date_earned'],
                             hours_worked=paycheck_data['hours_worked'],
                            )
                p.save()
                return HttpResponseRedirect('/paychecks/')
    else:
        return render(request,
                      'enter_paycheck.html',
                      {'form': EnterPaycheckForm()}
                     )


@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/signup/')
@require_http_methods(['GET', 'POST'])
def edit_paycheck(request, *args):
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    # split paycheck url into (email, 'paycheck', year, month, day)
    paycheck_data_split = args[0].split('-')
    paycheck = Paycheck.objects.get(owner=emp,
                                    date_earned__year=paycheck_data_split[2],
                                    date_earned__month=paycheck_data_split[3],
                                    date_earned__day=paycheck_data_split[4])

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

    form = EditPaycheckForm(initial={'paycheck': paycheck})
    return render(request, 'edit_paycheck.html', {'form': form, 'paycheck': paycheck})


# May not ever need to delete a paycheck
@login_required(login_url='/login/')
@permission_required('use_paychecks', login_url='/signup/')
def delete_paycheck(request):
    pass

@login_required(login_url='/login/')
@permission_required('use_expenses', login_url='/signup/')
@require_http_methods(['GET', 'POST'])
def enter_expenses(request):
    '''
    On POST request, get expenses data from form and update db.
    On GET request, show enter_expenses template/form.
    '''
    if request.method == 'POST':
        form = EnterExpenseForm(request.POST)
        if form.is_valid():
            u = TipoutUser.objects.get(email=request.user)
            emp = Employee.objects.get(user=u)

            expense_data = form.cleaned_data
            dupe = Expense.objects.filter(
                       owner=emp
                   ).filter(
                       expense_name=expense_data['expense_name'].lower()
                   )
            if dupe:
                return render(request,
                              'enter_expenses.html',
                              {'form': EnterExpenseForm(),
                               'error_message': 'An expense with that name already exists.'})
            else:
                e = Expense(owner=emp,
                            cost=expense_data['cost'],
                            expense_name=expense_data['expense_name'].lower(),
                            frequency=expense_data['frequency']
                           )
                e.save()
                return HttpResponseRedirect('/expenses/')
    else:
        form = EnterExpenseForm()
        return render(request, 'enter_expenses.html', {'form': form})

@login_required(login_url='/login/')
@permission_required('use_expenses', login_url='/signup/')
@require_http_methods(['GET'])
def expenses(request):
    '''
    Get expenses that belong to current user and pass them to the template.
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    expenses = Expense.objects.filter(owner=emp)
    return render(request, 'expenses.html', {'expenses': expenses})

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

        tips = Tip.objects.filter(owner=emp,
                                  date_earned__month=now().date().month).order_by('date_earned')[::-1]
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
@require_http_methods(['GET'])
def budget(request):
    '''
    Get TipoutUser from request context, then get tips belonging to that user
    and pass the daily average for past 30 days to template.

    Since budget is first view upon login, check to see if user is 'new'.
    If so, and it has been less than 30 days since signup, calculate tips
    based on init_daily_avg_tips. Otherwise, calculate based on actual tips.
    '''

    '''
    If user is new, send to new-user-setup to set init_avg_daily_tips.
    '''

    # get user, employee
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    # if user is new, send to new-user-setup
    if emp.new_user:
        return HttpResponseRedirect('/new-user-setup/')

    else:
        # expenses, daily expense cost - assuming every expense is paid monthly
        expenses = Expense.objects.filter(owner=emp)
        daily_expense_cost = sum([ exp.cost for exp in expenses ]) / 30

        # expenditures for the day
        expenditures_today_query = Expenditure.objects.filter(owner=emp, date=now().date())
        expenditures_today = sum([ exp.cost for exp in expenditures_today_query ])

        # get tips for last 30 days
        # not sure if order_by is ascending or descending
        tips = Tip.objects.filter(owner=emp).order_by('date_earned')[:30]
        tip_values = [ tip.amount for tip in tips ]

        # user's paychecks
        paychecks = Paycheck.objects.filter(owner=emp)
        # paycheck_amts = [ paycheck.amt for paycheck in paychecks ]
        # daily_avg_from_paycheck = (sum(paycheck_amts) / len(paycheck_amts))

        def pretty_dollar_amount(budget):
            pass

        if (now().date() - emp.signup_date).days <= 30:
            budget = avg_daily_tips_initial(emp.init_avg_daily_tips, tip_values, emp.signup_date) + daily_avg_from_paycheck(paychecks) - daily_expense_cost - expenditures_today
            budget_formatted = '{0:.2f}'.format(budget)
            return render(request, 'budget.html', {'avg_daily_tips': emp.init_avg_daily_tips, 'budget': budget_formatted})

        else:
            budget = avg_daily_tips(tip_values) + daily_avg_from_paycheck(paychecks) - daily_expense_cost - expenditures_today
            budget_formatted = '{0:.2f}'.format(budget)
            return render(request, 'budget.html', {'avg_daily_tips': avg_daily_tips(tip_values), 'budget': budget_formatted})

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
                       date=now().date()
                   ).filter(
                       note=exp_data['note'].lower()
                   )
            if dupe:
                return render(request,
                              'enter_expenditure.html',
                              {'form': EnterExpenditureForm(initial={'date': now().date()}),
                               'error_message': 'An expenditure with that note already exists.'}
                              )
            else:
                e = Expenditure(owner=emp, cost=exp_data['cost'], date=exp_data['date'], note=exp_data['note'].lower())
                e.save()
                return HttpResponseRedirect('/expenditures/')
    else:
        return render(request,
                      'enter_expenditure.html',
                      {'form': EnterExpenditureForm(initial={'date': now().date()})}
                      )

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
#     es = Expenditure.objects.filter(owner=u).filter(date=now().date())
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
def delete_expenditure(request, *args):
    # exp = args[0].replace('-', ' ')

    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        es = Expenditure.objects.filter(owner=emp).filter(date=now().date())
        e = None
        test = None
        for exp in es:
            if strip(exp.get_absolute_url(), '/') == args[0]:
                e = exp
        e.delete()
        return HttpResponseRedirect('/expenditures/')

@login_required(login_url='/login/')
@permission_required('use_expenditures', login_url='/signup/')
@require_http_methods(['GET'])
def expenditures(request):
    '''
    Default expenditures page show TODAY'S expenditures.
    '''
    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    exps = Expenditure.objects.filter(owner=emp).filter(date=now().date())
    return render(request, 'expenditures.html', {'exps': exps})

@login_required(login_url='/login/')
def edit_expense(request, *args):
    exp_name = args[0].replace('-', ' ')

    u = TipoutUser.objects.get(email=request.user)
    emp = Employee.objects.get(user=u)

    e = Expense.objects.filter(owner=emp).get(expense_name=exp_name)

    if request.method == 'GET':
        form = EditExpenseForm(initial={'cost': e.cost})
        return render(request, 'edit_expense.html', {'form': form, 'expense_name': e.expense_name})

    if request.method == 'POST':
        form = EditExpenseForm(request.POST)
        if form.is_valid():
            exp_data = form.cleaned_data
            ##
            # Need to check for dupe here
            ##
            exp = Expense.objects.get(owner=emp, expense_name=e.expense_name)
            exp.cost = exp_data['cost']
            exp.save()
            return HttpResponseRedirect('/expenses/')

@login_required(login_url='/login/')
def delete_expense(request, *args):
    exp_name = args[0].replace('-', ' ')

    if request.method == 'POST':
        u = TipoutUser.objects.get(email=request.user)
        emp = Employee.objects.get(user=u)

        e = Expense.objects.get(owner=emp, expense_name=exp_name)
        e.delete()
        return HttpResponseRedirect('/expenses/')

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
