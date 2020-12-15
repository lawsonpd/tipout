# tipout
A daily budgeting tool for employees who earn tips

## Purpose
For servers, bartenders and anyone else who earns tips as all or part of their income, budgeting can be challenging since earnings are unpredictable and can vary month-to-month, week-to-week and day-to-day. When I was a server, I tried using a spreadsheet to track earnings and manage spending, but this was not a good user experience and was more complicated than I wanted to tolerate.

I simply wanted to know what my earnings were, what my spending looked like and, importantly, what I could spend on a given day while also saving enough to pay my recurring bills[<sup id="footnote">1</sup>](#fn1). So, I built an app with a simple UI that would perform these basic functions.

## Features
- automatic daily budget based on past earnings and recurring expenses
- record earnings (tips and paychecks)
- record expenses (i.e. recurring bills or payments) and expenditures (i.e. one-off spending)
- view daily and weekly spending patterns
- view monthly earnings patterns

## Build
- Django
- Postgresql
- Memcached
- Stripe

## Present/future
As a solo (and somewhat novice) developer, I didn't feel confident taking it into production or launching commercially. Since this is a financial product that could negatively impact users if there were calculation bugs that went uncaught, I didn't want to take the risk. There were unimplemented features that I felt would be critical for user adoption and much testing still needed. I put aside the project after working on it for countless hours over several months.

I still believe it's a product that serves a real need, as I had this need myself, and although it never saw its way into the hands of real users, I have no regrets about putting in the effort. I learned a lot about product management (using tools like Trello to track feature development), UI/UX and SDLC.

### Footnotes
<span id="fn1"></span> [1](#footnote). I can't defend this as an optimal way to budget, but at the time it worked for me.