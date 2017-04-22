from tipout.models import Tip, Expenditure, Expense, Paycheck, Budget
from django.contrib.contenttypes.models import ContentType

tip_content_type = ContentType.objects.get_for_model(Tip)
tip_permission = Permission.objects.create(
    codename='use_tips',
    name='Can add and edit tips',
    content_type=tip_content_type,
)

expenditure_content_type = ContentType.objects.get_for_model(Expenditure)
expenditure_permission = Permission.objects.create(
    codename='use_expenditures',
    name='Can add and edit expenditures',
    content_type=expenditure_content_type,
)

expense_content_type = ContentType.objects.get_for_model(Expense)
expense_permission = Permission.objects.create(
    codename='use_expenses',
    name='Can add and edit expenses',
    content_type=expense_content_type,
)

paycheck_content_type = ContentType.objects.get_for_model(Paycheck)
paycheck_permission = Permission.objects.create(
    codename='use_paychecks',
    name='Can add and edit paychecks',
    content_type=paycheck_content_type,
)

budget_content_type = ContentType.objects.get_for_model(Budget)
budget_permission = Permission.objects.create(
    codename='use_budget',
    name='Can access budget',
    content_type=budget_content_type,
)
