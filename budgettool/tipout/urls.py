from django.conf.urls import url, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^enter-tips/$', views.enter_tips, name='enter-tips'),
    # url(r'^edit-tips/$', views.edit_tips, name='edit-tips'),
    url(r'^tips/$', views.tips, name='tips'),
    url(r'^user-test/$', views.user_test, name='user-test'),
    url(r'^budget/$', views.budget, name='budget'),
    url(r'^expenses/$', views.expenses, name='expenses'),
    url(r'^enter-expenses/$', views.enter_expenses, name='enter-expenses'),
    url(r'^edit-expense/$', views.edit_expense, name='edit-expense-submit'),
    url(r'^edit-expense/([a-z-A-z]+)/$', views.edit_expense, name='edit-expense'),
    url(r'^delete-expense/([a-z-A-z]+)/$', views.delete_expense, name='delete-expense'),
    url(r'^enter-expenditure/$', views.enter_expenditure, name='enter-expenditure'),
    # url(r'^edit-expenditure/([0-9]+)/$', views.edit_expenditure, name='edit-expenditure'),
    url(r'^expenditures/$', views.expenditures, name='expenditures'),
    url(r'^expenditures/([0-9]{4})/$', views.expenditures_year_archive, name='expenditures-year-archive'),
    url(r'^expenditures/([0-9]{4})/([0-9]{2})/$', views.expenditures_month_archive, name='expenditures-month-archive'),
    url(r'^expenditures/([0-9]{4})/([0-9]{2})/([0-9]+)/$', views.expenditures_day_archive, name='expenditures-day-archive'),
    url(r'^expenditures/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]+)/(?P<exp>[0-9]+)$', views.expenditure_detail, name='expenditure-detail'),
    url(r'^new-user-setup/$', views.new_user_setup, name='new-user-setup'),
    url(r'^register/$',
        views.register,
        {'template_name': 'registration/register.html'}
    ),
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
]
