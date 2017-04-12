from django.contrib.auth.models import Permission, Group

Subscribers = Group.objects.create(name='subscribers')
Subscribers.permissions.add('use_tips',
                            'use_expenditures',
                            'use_expenses',
                            'use_paychecks',
                            'use_budget',
)
