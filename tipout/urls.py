from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^enter-tips/$', views.enter_tips, name='enter-tips'),
    # url(r'^edit-tips/(?P<tip_id>[0-9]+)/$', views.edit_tip, name='edit-tip'),
    url(r'^delete-tip/(?P<tip_id>[0-9]+)/$', views.delete_tip, name='delete-tip'),
    url(r'^tips/$', views.tips, name='tips'),
    url(r'^tips/archive/$', views.tips_archive, name='tips-archive'),
    url(r'^tips/archive/(?P<year>[0-9]{4})/$', views.tips_archive, name='tips-archive'),
    url(r'^tips/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/$', views.tips_archive, name='tips-archive'),
    url(r'^tips/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/$', views.tips_archive, name='tips-archive'),
    url(r'^tips/archive/$', views.tips_archive, name='tips-archive'),
    url(r'^budget/$', views.budget, name='budget'),
    url(r'^expenses/$', views.expenses, name='expenses'),
    url(r'^enter-expenses/$', views.enter_expenses, name='enter-expenses'),
    url(r'^edit-expense/$', views.edit_expense, name='edit-expense-submit'),
    url(r'^edit-expense/([a-z-A-Z]+)/$', views.edit_expense, name='edit-expense'),
    url(r'^delete-expense/([a-z-A-Z]+)/$', views.delete_expense, name='delete-expense'),
    url(r'^enter-expenditure/$', views.enter_expenditure, name='enter-expenditure'),
    url(r'^expenditures/$', views.expenditures, name='expenditures'),
    # url(r'^delete-expenditure/([a-z-A-Z-0-9]+)/([a-z-A-Z-0-9]+)/$', views.delete_expenditure, name='delete-expenditure'),
    url(r'^delete-expenditure/([a-z-A-Z-0-9]+)/$', views.delete_expenditure, name='delete-expenditure'),
    url(r'^expenditures/archive/$', views.expenditures_archive, name='expenditures-archive'),
    url(r'^expenditures/archive/(?P<year>[0-9]{4})/$', views.expenditures_year_archive, name='expenditures-year-archive'),
    url(r'^expenditures/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/$', views.expenditures_month_archive, name='expenditures-month-archive'),
    url(r'^expenditures/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/$', views.expenditures_day_archive, name='expenditures-day-archive'),
    url(r'^expenditures/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<exp>[a-z-A-Z]+)$', views.expenditure_detail, name='expenditure-detail'),
    url(r'^paychecks/$', views.paychecks, name='paychecks'),
    url(r'^enter-paycheck/$', views.enter_paycheck, name='enter-paycheck'),
    url(r'^edit-paycheck/([a-z-A-Z-0-9]+)/$', views.edit_paycheck, name='edit-paycheck'),
    # delete paycheck needs more expressive RE to identify specific paychecks (probably by date)
    #
    # would it be necessary to delete a paycheck?
    # url(r'^delete-paycheck/$', views.delete_paycheck, name='delete-paycheck'),
    #
    url(r'^new-user-setup/$', views.new_user_setup, name='new-user-setup'),
    # url(r'^register/$',
    #     views.register,
    #     {'template_name': 'registration/register.html'}
    # ),
    url(r'^signup/$',
        views.signup,
        {'template_name': 'registration/signup.html'}
    ),
    url(r'^thankyou/$', views.thank_you, name='thank-you'),
    url(
        r'^login/$',
        auth_views.login,
        {'template_name': 'registration/login.html'}
    ),
    url(
        r'^logout/$',
        auth_views.logout,
        {'template_name': 'registration/logout.html'}
    ),
    url('^', include('django.contrib.auth.urls')),
    url(
        r'^$',
        views.home,
        {'template_name': 'home.html'}
    ),
]
