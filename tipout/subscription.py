import stripe

stripe.api_key = 'sk_test_GVCFYxcWaAZq3zBnEifLXeJd'

plan = stripe.Plan.create(
    name='Basic Plan',
    id='basic-monthly',
    interval='month',
    currency='usd',
    amount=0
)
