from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

subscribers = Group.objects.create(name='subscribers')
subscribers.permissions.add('use_tips',
                            'use_expenditures',
                            'use_expenses',
                            'use_paychecks',
                            'use_budget',
)
