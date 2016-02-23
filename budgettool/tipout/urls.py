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
    url(r'^expenses/$', views.view_expenses, name='view-expenses'),
    url(r'^enter-expenses/$', views.enter_expenses, name='enter-expenses'),
    # url(r'^edit-expenses/$', views.edit_expenses, name='edit-expenses'),
    url(r'^enter-expenditure/$', views.enter_expenditure, name='enter-expenditure'),
    url(r'^expenditures/$', views.view_expenditures, name='view-expenditures'),
    url(r'^register/$', views.register, name='register'),
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
