from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

# from . import views
from . import budget, expenditures, expenses, general_views, paychecks, subscription, tips, subscription_test, savings, misc_income

urlpatterns = [
    url(r'^enter-tips/$', tips.enter_tips, name='enter-tips'),
    # url(r'^edit-tips/(?P<tip_id>[0-9]+)/$', tips.edit_tip, name='edit-tip'),
    url(r'^delete-tip/(?P<tip_id>[0-9]+)/$', tips.delete_tip, name='delete-tip'),
    url(r'^tips/$', tips.tips, name='tips'),
    url(r'^tips/archive/$', tips.tips_archive, name='tips-archive'),
    url(r'^tips/archive/(?P<year>[0-9]{4})/$', tips.tips_archive, name='tips-archive'),
    url(r'^tips/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/$', tips.tips_archive, name='tips-archive'),
    url(r'^tips/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/$', tips.tips_archive, name='tips-archive'),
    url(r'^tips/archive/$', tips.tips_archive, name='tips-archive'),
    url(r'^other-funds/$', misc_income.other_funds, name='other-funds'),
    url(r'^enter-other-funds/$', misc_income.enter_other_funds, name='enter-other-funds'),
    url(r'^delete-other-funds/(?P<funds_id>[0-9]+)/$', misc_income.delete_other_funds, name='delete-other-funds'),
    url(r'^budget/$', budget.budget, name='budget'),
    url(r'^balance/$', budget.balance, name='balance'),
    url(r'^edit-balance/$', budget.edit_balance, name='edit-balance'),
    url(r'^bhistory/$', budget.budget_history, name='budget-history'),
    url(r'^reset-budgets/$', budget.reset_budgets, name='reset-budgets'),
    url(r'^weekly-budget/$', budget.weekly_budget, name='weekly-budget'),
    url(r'^expenses/$', expenses.expenses, name='expenses'),
    url(r'^enter-expense/$', expenses.enter_expense, name='enter-expense'),
    url(r'^edit-expense/$', expenses.edit_expense, name='edit-expense-submit'),
    url(r'^edit-expense/([a-z-A-Z]+)/$', expenses.edit_expense, name='edit-expense'),
    url(r'^delete-expense/([a-z-A-Z]+)/$', expenses.delete_expense, name='delete-expense'),
    url(r'^pay-expense/$', expenses.pay_expense, name='pay-expense'),
    url(r'^pay-expense/(?P<exp>[0-9]+)/$', expenses.pay_expense, name='pay-expense-submit'),
    url(r'^enter-expenditure/$', expenditures.enter_expenditure, name='enter-expenditure'),
    url(r'^expenditures/$', expenditures.expenditures, name='expenditures'),
    url(r'^spending-profile/$', expenditures.spending_profile, name='spending-profile'),
    # url(r'^delete-expenditure/([a-z-A-Z-0-9]+)/([a-z-A-Z-0-9]+)/$', expenditures.delete_expenditure, name='delete-expenditure'),
    url(r'^delete-expenditure/(?P<exp>[0-9]+)/$', expenditures.delete_expenditure, name='delete-expenditure'),
    url(r'^edit-expenditure/(?P<exp>[0-9]+)/$', expenditures.edit_expenditure, name='edit-expenditure'),
    url(r'^expenditures/archive/$', expenditures.expenditures_archive, name='expenditures-archive'),
    url(r'^expenditures/archive/(?P<year>[0-9]{4})/$', expenditures.expenditures_year_archive, name='expenditures-year-archive'),
    url(r'^expenditures/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/$', expenditures.expenditures_month_archive, name='expenditures-month-archive'),
    url(r'^expenditures/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/$', expenditures.expenditures_day_archive, name='expenditures-day-archive'),
    url(r'^expenditures/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<exp>[a-z-A-Z]+)$', expenditures.expenditure_detail, name='expenditure-detail'),
    url(r'^paychecks/$', paychecks.paychecks, name='paychecks'),
    url(r'^paychecks-archive/$', paychecks.paychecks_archive, name='paychecks-archive'),
    url(r'^enter-paycheck/$', paychecks.enter_paycheck, name='enter-paycheck'),
    url(r'^edit-paycheck/(?P<p>[0-9]+)/$', paychecks.edit_paycheck, name='edit-paycheck'),
    # delete paycheck needs more expressive RE to identify specific paychecks (probably by date)
    #
    # would it be necessary to delete a paycheck?
    url(r'^delete-paycheck/(?P<p>[0-9]+)/$', paychecks.delete_paycheck, name='delete-paycheck'),
    url(r'^savings/$', savings.savings, name='savings'),
    url(r'^savings-setup/$', savings.savings_setup, name='savings-setup'),
    url(r'^savings-transaction/$', savings.savings_transaction, name='deposit-withdraw-savings'),
    url(r'^savings-transaction-history/$', savings.savings_transaction_history, name='savings-transaction-history'),
    #
    url(r'^new-user-setup/$', general_views.new_user_setup, name='new-user-setup'),
    # url(r'^register/$',
    #     subscription.register,
    #     {'template_name': 'registration/register.html'}
    # ),
    # url(r'^signup/$',
    #     subscription.signup,
    #     {'template_name': 'registration/signup.html'}
    # ),
    url(r'^thankyou/$', subscription.thank_you, name='thank-you'),
    url(r'^subscription/$', subscription.manage_subscription, name='manage-subscription'),
    url(r'^cancel-subscription/$', subscription.cancel_subscription, name='cancel-subscription'),
    url(r'^expired/$', subscription.demo_expired, name='demo-expired'),
    url(r'^feedback/$', general_views.feedback, name='feedback'),
    url(
        r'^login/$',
        auth_views.login,
        {'template_name': 'registration/demo-login.html'}
    ),
    url(
        r'^logout/$',
        auth_views.logout,
        {'template_name': 'registration/logout.html'}
    ),
    url('^', include('django.contrib.auth.urls')),
    url(
        r'^$',
        general_views.home,
        {'template_name': 'demo-home.html'}
    ),
    # url(r'^signup-test/$',
    #     subscription_test.signup_test,
    #     {'template_name': 'registration/signup_test.html'}
    # ),
    # url(r'^how-it-works/$', general_views.how_it_works, name='how-it-works'),
    url(r'^faq/$', general_views.faq, name='faq'),
    url(r'^add-to-homescreen/$', general_views.add_to_homescreen, name='add-to-homescreen'),
]
