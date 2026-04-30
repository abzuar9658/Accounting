# Accounting

A small Django app for tracking earnings and expenses across several people
who share monthly profit splits with a company entity.

The core idea is **earning ≠ ownership**: money received by one person is
redistributed each month by configurable percentages, and the app keeps
track of who still owes whom.

## Stack

- Django 5.x · Python 3.12
- PostgreSQL 16
- Tailwind CSS (CDN, with the forms and typography plugins)
- Docker Compose for local development

All currency is **PKR**. Calculations use 3 decimal places, display uses 2.

## Requirements

- Docker Desktop (or Docker Engine + Compose v2)
- `git`

That's it — Python and Postgres run inside the containers.

## First-time setup

```bash
# 1. clone & enter the repo
git clone <url> accounting
cd accounting

# 2. create your local .env from the template
cp .env.example .env
# edit .env and replace DJANGO_SECRET_KEY with a long random string,
# e.g. python -c "import secrets; print(secrets.token_urlsafe(64))"

# 3. build the image
docker compose build

# 4. start the database, run migrations, create your admin user
docker compose up -d db
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py createsuperuser

# 5. run the dev server
docker compose up
```

Open <http://localhost:8000/> and sign in.

## Day-to-day commands

```bash
docker compose up                # start everything (web on :8000)
docker compose down              # stop everything
docker compose logs -f web       # tail web logs

# Django management commands run through the web container:
docker compose run --rm web python manage.py makemigrations
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py shell
docker compose run --rm web python manage.py createsuperuser
```

## Project layout

```
apps/
  accounts/    # User (custom) + Person + login/logout + role groups
  audit/       # Thread-local actor middleware + signal-based AuditLog
  common/      # Shared template tags (money, roles)
  company/     # Company singleton + BalanceMovement ledger
  dashboard/   # Read-only aggregations + monthly report
  earnings/    # Earnings + per-participant Allocations
  expenses/    # ExpenseCategory + Expense (auto-posts to ledger)
  periods/     # Month + SplitRule + SplitShare + open/review/closed lifecycle
  transfers/   # Settlement engine + Transfer + partial Payments
config/        # settings (base/dev), urls, wsgi/asgi
templates/     # project-level base + per-app templates
```

## How the pieces fit together

1. An admin creates a **Month** and configures its **SplitRule** (shares
   that sum to 100%, including the Company).
2. **Earnings** are recorded against the month. Each earning auto-generates
   per-participant **Allocation** rows from the active split rule.
3. **Expenses** are recorded against the month and post a negative
   movement onto the company ledger automatically.
4. When a month is ready, an admin clicks **Settle month**. The settlement
   engine nets every (from, to) pair into the minimum number of
   **Transfers**, accounting for any **Payments** already recorded so
   re-running settlement is safe.
5. Members record **Payments** against transfers (full or partial). The
   amounts also post onto the company ledger when they involve the
   company.
6. Pending or partial transfers from prior months keep showing up on the
   dashboard until they're fully paid — this is how unsettled balances
   "carry forward".

## Roles

Two role groups are seeded automatically: **Admin** and **Member**.

- **Admin**: manage people, set split rules, create/edit earnings and
  expenses, settle months, transition months between
  open / review / closed, and view the audit log.
- **Member**: view their own data, record payments, upload proof.

Superusers can do everything regardless of group.

## Month lifecycle

| Status | Editable | Allowed transitions |
|--------|----------|---------------------|
| Open | yes | → review, → closed |
| Under review | yes | → open, → closed |
| Closed | no | → open (reopen) |

When a month is closed, earnings/expenses/split rule become read-only.
Transfers and payments remain visible and payments can still be recorded.

## Audit trail

Every create/update/delete on the principal models (Person, Company,
BalanceMovement, Month, SplitRule, SplitShare, Earning, Expense, Transfer,
Payment) is logged with the acting user and a per-field diff. Admins can
view the log at `/audit/` or via the Django admin.

## Settings & secrets

All secrets live in `.env` (gitignored). `.env.example` lists every
variable with safe defaults. The Postgres container reads the same file.

## Tests

There are no tests checked in yet — the app has been validated with
manual smoke scripts during development. To run Django's checks:

```bash
docker compose run --rm web python manage.py check
```
