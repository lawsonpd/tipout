from datetime import date

def pretty_date(timestamp):
  return date.fromtimestamp(timestamp).strftime('%B %d %Y')

def pretty_dollar_amount(amount):
  '''
  This only works if amount is multiple of 100 (e.g. '500')
  '''
  return '$' + '{0:.2f}'.format(amount/100)
