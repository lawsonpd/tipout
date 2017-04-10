import stripe

stripe.api_key = 'sk_test_GVCFYxcWaAZq3zBnEifLXeJd'

basic_plan = stripe.Plan.create(
    name='Free Plan',
    id='free-plan',
    interval='month',
    currency='usd',
    amount=0,
)

premium_plan = stripe.Plan.create(
    name='Paid Plan',
    id='paid-plan',
    interval='month',
    currency='usd',
    amount='500',
)
