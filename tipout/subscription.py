import stripe

stripe.api_key = 'sk_test_GVCFYxcWaAZq3zBnEifLXeJd'

<<<<<<< HEAD
plan = stripe.Plan.create(
    name='Basic Plan',
    id='basic-monthly',
    interval='month',
    currency='usd',
    amount=0
=======
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
>>>>>>> subscriptions
)
