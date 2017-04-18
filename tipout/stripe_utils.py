from datetime import date, timedelta

def pretty_date(timestamp):
  return date.fromtimestamp(timestamp).strftime('%B %d %Y')

def pretty_dollar_amount(amount):
  '''
  This only works if amount is multiple of 100 (e.g. '500')
  '''
  return '$' + '{0:.2f}'.format(amount/100)

def refund_approved(next_invoice_date):
    '''
    Must cancel at least 2 weeks before next invoice.

    If there are fewer than 2 weeks until next_invoice_date,
    then return False (i.e. no refund), else return True (refund).
    '''

    if date.fromtimestamp(next_invoice_date) - date.today() > timedelta(14):
        return True
    else:
        return False

def most_recent_invoice(invoices):
    '''
    Order by date
    '''
    sorted_invoices = sorted(invoices, cmp=lambda x,y: cmp(x.date, y.date), reverse=True)
    return sorted_invoices[0]
