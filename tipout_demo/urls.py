from django.urls import path, include
from django.contrib.auth import login as auth_login, logout as auth_logout

# from . import views
from . import budget, expenditures, expenses, general_views, paychecks, subscription, tips, subscription_test, savings, misc_income

urlpatterns = [
    path('enter-tips/', tips.enter_tips, name='enter-tips'),
    # path('edit-tips/<int:tip_id>/', tips.edit_tip, name='edit-tip'),
    path('delete-tip/<int:tip_id>/', tips.delete_tip, name='delete-tip'),
    path('tips/', tips.tips, name='tips'),
    path('tips/archive/', tips.tips_archive, name='tips-archive'),
    path('tips/archive/<int:year>/', tips.tips_archive, name='tips-archive'),
    path('tips/archive/<int:year>/<int:month>/', tips.tips_archive, name='tips-archive'),
    path('tips/archive/<int:year>/<int:month>/<int:day>/', tips.tips_archive, name='tips-archive'),
    path('tips/archive/', tips.tips_archive, name='tips-archive'),
    path('other-funds/', misc_income.other_funds, name='other-funds'),
    path('enter-other-funds/', misc_income.enter_other_funds, name='enter-other-funds'),
    path('delete-other-funds/<int:funds_id>/', misc_income.delete_other_funds, name='delete-other-funds'),
    path('budget/', budget.budget, name='budget'),
    path('balance/', budget.balance, name='balance'),
    path('edit-balance/', budget.edit_balance, name='edit-balance'),
    path('bhistory/', budget.budget_history, name='budget-history'),
    path('reset-budgets/', budget.reset_budgets, name='reset-budgets'),
    path('weekly-budget/', budget.weekly_budget, name='weekly-budget'),
    path('expenses/', expenses.expenses, name='expenses'),
    path('enter-expense/', expenses.enter_expense, name='enter-expense'),
    path('edit-expense/', expenses.edit_expense, name='edit-expense-submit'),
    path('edit-expense/<int:pk>/', expenses.edit_expense, name='edit-expense'),
    path('delete-expense/<int:pk>/', expenses.delete_expense, name='delete-expense'),
    path('pay-expense/', expenses.pay_expense, name='pay-expense'),
    path('pay-expense/<int:exp>/', expenses.pay_expense, name='pay-expense-submit'),
    path('enter-expenditure/', expenditures.enter_expenditure, name='enter-expenditure'),
    path('expenditures/', expenditures.expenditures, name='expenditures'),
    path('spending-profile/', expenditures.spending_profile, name='spending-profile'),
    # path('delete-expenditure/([a-z-A-Z-0-9]+)/([a-z-A-Z-0-9]+)/$', expenditures.delete_expenditure, name='delete-expenditure'),
    path('delete-expenditure/<int:exp>/', expenditures.delete_expenditure, name='delete-expenditure'),
    path('edit-expenditure/<int:exp>/', expenditures.edit_expenditure, name='edit-expenditure'),
    path('expenditures/archive/', expenditures.expenditures_archive, name='expenditures-archive'),
    path('expenditures/archive/<int:year>/', expenditures.expenditures_year_archive, name='expenditures-year-archive'),
    path('expenditures/archive/<int:year>/<int:month>/', expenditures.expenditures_month_archive, name='expenditures-month-archive'),
    path('expenditures/archive/<int:year>/<int:month>/<int:day>/', expenditures.expenditures_day_archive, name='expenditures-day-archive'),
    path('expenditures/archive/<int:year>/<int:month>/<int:day>/<int:exp>', expenditures.expenditure_detail, name='expenditure-detail'),
    path('paychecks/', paychecks.paychecks, name='paychecks'),
    path('paychecks-archive/', paychecks.paychecks_archive, name='paychecks-archive'),
    path('enter-paycheck/', paychecks.enter_paycheck, name='enter-paycheck'),
    path('edit-paycheck/<int:p>/', paychecks.edit_paycheck, name='edit-paycheck'),
    # delete paycheck needs more expressive RE to identify specific paychecks (probably by date)
    #
    # would it be necessary to delete a paycheck?
    path('delete-paycheck/<int:p>/', paychecks.delete_paycheck, name='delete-paycheck'),
    path('savings/', savings.savings, name='savings'),
    path('savings-setup/', savings.savings_setup, name='savings-setup'),
    path('savings-transaction/', savings.savings_transaction, name='deposit-withdraw-savings'),
    path('savings-transaction-history/', savings.savings_transaction_history, name='savings-transaction-history'),
    #
    path('new-user-setup/', general_views.new_user_setup, name='new-user-setup'),
    # path('register/',
    #     subscription.register,
    #     {'template_name': 'registration/register.html'}
    # ),
    # path('signup/',
    #     subscription.signup,
    #     {'template_name': 'registration/signup.html'}
    # ),
    path('thankyou/', subscription.thank_you, name='thank-you'),
    path('subscription/', subscription.manage_subscription, name='manage-subscription'),
    path('cancel-subscription/', subscription.cancel_subscription, name='cancel-subscription'),
    path('expired/', subscription.demo_expired, name='demo-expired'),
    path('feedback/', general_views.feedback, name='feedback'),
    path(
        'login/',
        auth_login,
        {'template_name': 'registration/demo-login.html'}
    ),
    path(
        'logout/',
        auth_logout,
        {'template_name': 'registration/logout.html'}
    ),
    path('', include('django.contrib.auth.urls')),
    path(
        '',
        general_views.home,
        {'template_name': 'demo-home.html'}
    ),
    # path('signup-test/',
    #     subscription_test.signup_test,
    #     {'template_name': 'registration/signup_test.html'}
    # ),
    # path('how-it-works/', general_views.how_it_works, name='how-it-works'),
    path('faq/', general_views.faq, name='faq'),
    path('add-to-homescreen/', general_views.add_to_homescreen, name='add-to-homescreen'),
]
