Below is a clear requirements draft.

# Simple Accounting & Profit Split App Requirements

## 1. Purpose

Build an app that tracks earnings, profit sharing, company balance, expenses, and monthly settlements between multiple people and the company.

The app should make it very clear:

Who earned how much.

How much belongs to each person.

How much belongs to the company.

How much money still needs to be transferred.

Which payments are pending or completed.

How company expenses affect the company balance.

## 2. Main Entities

### Person

Example:

Person 1

Person 2

Future: Person 3, Person 4, etc.

Each person should have:

Name

Bank/account details

Status: active/inactive

Earnings history

Share received

Pending amount

Paid amount

### Company

The company has:

Initial balance

Monthly company share from earnings

Expenses

Current balance

Bank/account details

### Earning

An earning is money received from work/profile/client.

Each earning should store:

Earning month

Earned by which person/profile

Amount received

Receiving account

Split rule used

Amount allocated to each person

Amount allocated to company

Payment status

Notes/reference

Example:

P1 earns 500,000 PKR in January.

Split: 40% P1, 40% P2, 20% Company.

Result:

P1 gets 200,000

P2 gets 200,000

Company gets 100,000

## 3. Split Rules

Default monthly split:

Person 1: 40%

Person 2: 40%

Company: 20%

But split can change month by month.

Example:

January: 40 / 40 / 20

February: 33 / 33 / 34

March: 50 / 30 / 20

Rules:

Each month must have one active split rule.

Total percentage must always equal 100%.

Split rule can include any number of people plus company.

Once a month is closed, split should not be editable unless reopened by admin.

## 4. Monthly Accounting Flow

For each month:

Add earnings for each person/profile.

Apply the month’s split rule.

Calculate how much each person should receive.

Calculate how much company should receive.

Show pending transfers.

User marks transfers as paid/done.

Company expenses are deducted from company balance.

Month can be closed after everything is reviewed.

## 5. Transfer Tracking

The app should not just calculate shares; it should track actual movement of money.

For each calculated amount, create a payable/receivable record.

Example:

P1 earned 500,000 but money landed in P1’s bank account.

Split says:

P1 owns 200,000

P2 owns 200,000

Company owns 100,000

So app should show:

P1 keeps 200,000

P1 needs to transfer 200,000 to P2

P1 needs to transfer 100,000 to Company

Each transfer should have:

From account

To account

Amount

Due month

Status: pending / paid / cancelled

Payment date

Proof/reference

Notes

## 6. Company Balance

Company balance starts with an initial balance.

Company balance increases by:

Company share from monthly earnings

Manual deposits

Adjustments

Company balance decreases by:

Company expenses

Withdrawals

Adjustments

Formula:

Company Closing Balance = Opening Balance + Company Income - Company Expenses

## 7. Expenses

All expenses are paid by the company only.

Expense fields:

Date

Month

Category

Amount

Paid from company account

Description

Receipt/proof optional

Created by

Examples:

Software subscription

Laptop

Internet

Office rent

Marketing

Taxes

Bank charges

## 8. Dashboard

Dashboard should show:

Current company balance

Total earnings this month

Total company share this month

Total expenses this month

Net company balance movement

Amount payable to each person

Pending transfers

Completed transfers

Month status: open / closed

## 9. Monthly Report

For every month, generate a clear report:

Example January Report:

Total Earnings:

P1 earned: 500,000

P2 earned: 1,000,000

Total: 1,500,000

Split Rule:

P1: 40%

P2: 40%

Company: 20%

Final Allocation:

P1 total share: 600,000

P2 total share: 600,000

Company share: 300,000

Company Expenses:

Total expenses: 80,000

Company Net Increase:

300,000 - 80,000 = 220,000

Transfers:

P1 → P2: paid/pending

P1 → Company: paid/pending

P2 → P1: paid/pending

P2 → Company: paid/pending

Closing Company Balance:

Opening balance + 220,000

## 10. Important Accounting Logic

The app should separate these concepts:

Earning received

Ownership after split

Actual transfer/payment

Company expense

Company balance

This is very important.

Just because money lands in P1’s bank does not mean all of it belongs to P1.

The app should calculate what belongs to whom, then track who still needs to transfer money.

## 11. User Roles

### Admin

Can manage people

Can set split rules

Can add/edit earnings

Can add/edit expenses

Can close/reopen months

Can see all reports

### Person/User

Can see their own earnings

Can see what they need to receive

Can see what they need to pay

Can mark transfer as paid if allowed

Can upload proof

## 12. Month Closing

Each month should have status:

Open

Under review

Closed

When closed:

Earnings cannot be changed

Split cannot be changed

Expenses cannot be changed

Transfers remain visible

Admin can reopen month if correction is needed.

## 13. Audit Trail

Every important action should be logged:

Who added earning

Who changed split

Who added expense

Who marked transfer as paid

Who closed the month

Old value and new value

Timestamp

This makes the app trustworthy.

## 14. MVP Screens

Minimum app should have:

Dashboard

People management

Company balance

Monthly split settings

Earnings entry

Expense entry

Transfer/payments page

Monthly report

Audit log

## 15. Example Calculation

P1 earns 500,000.

P2 earns 1,000,000.

Total earnings = 1,500,000.

Split = 40 / 40 / 20.

P1 share = 600,000.

P2 share = 600,000.

Company share = 300,000.

But actual money received:

P1 received 500,000.

P2 received 1,000,000.

Final ownership:

P1 should have 600,000.

P2 should have 600,000.

Company should have 300,000.

So settlement required:

P2 has extra 400,000.

P1 needs 100,000 more.

Company needs 300,000.

Therefore:

P2 transfers 100,000 to P1.

P2 transfers 300,000 to Company.

After that, all balances are correct.

## 16. Core Goal

The app should answer these questions at any time:

How much did each person earn?

How much does each person actually own?

Who needs to pay whom?

How much belongs to the company?

What is the current company balance?

What expenses were paid?

Which month is fully settled?

Which transfers are still pending?
