# HomeMeter: Household Energy & Water Monitor

A menu-driven command-line app that helps Rwandan households record their electricity and water meter readings, see what they used and what it cost under the block tariffs, and get warned before their usage jumps into a more expensive block.

Built by Team 6 (BSE Year 1, Cohort 1) for Peer Learning Project 2. GCGOs: Climate Change, Infrastructure, Natural Resource Management.

## Why

- 85.4% of Rwandan households had electricity by the end of 2025 (REG).
- Since 1 October 2025, the first 20 kWh a month cost 89 RWF per kWh, units 21 to 50 cost 310 RWF and every unit above 50 costs 369 RWF. Going from 20 to 21 kWh makes each extra unit almost 3.5 times more expensive.
- Most prepaid users never track their meter, so they cross into the expensive blocks without noticing. Water is billed in rising blocks too.

## How to run

Requires **Python 3.11 or newer**. Only the standard library is used (`sqlite3`, `hashlib`, `getpass`, `logging`, `unittest`), so nothing needs installing.

```bash
git clone git@github.com:alustudent/homemeter.git
cd homemeter

python3 seed_demo.py     # optional: demo accounts and five months of readings
python3 main.py          # start the app
python3 -m unittest -v   # run the 35 tests
```

On the very first run without demo data, the app asks you to create the admin account.

Demo accounts created by `seed_demo.py` (for the presentation only):

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin2026` |
| Household (Mugisha Family, Gasabo) | `mugisha` | `Mugisha2026` |
| Household (Uwase Family, Kicukiro) | `uwase` | `Uwase2026` |

To start again from scratch, delete `homemeter.db` and run `seed_demo.py` again.

## User roles

| Role | What they can do |
|---|---|
| **Admin** (utility or estate manager) | Create, edit and delete households; create household and admin accounts, reset passwords, delete accounts; change tariff prices; open any household's readings and reports; see an overview of every household for a month. |
| **Household** (family or tenant) | Record electricity and water readings; view, edit and delete their own readings; monthly usage and cost report; 6-month history; usage alerts with saving tips; change their password. A household can never see another household's data. |

## Menus

```
WELCOME TO HOMEMETER          HOUSEHOLD MENU                         ADMIN MENU
 1. Log in                     1. Record a meter reading              1. Manage households
 0. Exit program               2. View monthly usage & cost report    2. Manage user accounts
                               3. Check usage alerts & saving tips    3. Manage tariffs
                               4. Manage my readings                  4. Open a household
                               5. View usage history (6 months)       5. All households overview
                               6. Change my password                  6. Change my password
                               0. Log out                             0. Log out
```

## Architecture

Each layer has one job and only talks to the layer below it.

```
main.py                                starts logging, opens the database, runs the app
  └─ app/cli/                          menus: read the keyboard, print results, never touch SQL
       └─ app/services/                rules: validation, permissions, usage, cost, alerts
            └─ app/repositories/       the only code that writes SQL
                 └─ app/database.py    SQLite connection, schema, transactions
```

| Path | What it holds |
|---|---|
| `main.py` | Entry point |
| `seed_demo.py` | Demo data for the presentation |
| `app/config.py` | Settings: database path, tariffs, thresholds, districts, saving tips |
| `app/models.py` | Classes: `User`, `Household`, `MeterReading`, `TariffBlock`, `UsageLine`, and the `Role` and `Utility` enums |
| `app/errors.py` | Error classes whose messages are safe to show the user |
| `app/permissions.py` | `require_admin` and `require_household_access` |
| `app/database.py` | `Database`: schema, default tariffs, `transaction()` |
| `app/security.py` | Password hashing (PBKDF2-SHA256 with a random salt) |
| `app/repositories/` | One repository per table: users, households, readings, tariffs |
| `app/services/` | `AuthService`, `HouseholdService`, `ReadingService`, `TariffService`, `ReportService`, `AlertService` |
| `app/cli/` | `prompts.py` (safe input helpers and menu loop), one menu module per feature, `app.py` (routes each role) |
| `tests/` | 35 `unittest` tests, one file per feature |

## Database

SQLite file `homemeter.db`, created on first run. No CSV or JSON files are used. Every ID is a UUID.

| Table | Columns | Rules |
|---|---|---|
| `households` | id, name, district, people, created_at | `people > 0` |
| `users` | id, username, password_hash, salt, role, household_id, created_at | unique username; a household account must point to a household, an admin must not; deleting a household deletes its accounts |
| `readings` | id, household_id, utility, value, read_on, created_at | one reading per household, utility and day; `value >= 0`; deleting a household deletes its readings |
| `tariff_blocks` | id, utility, lower_units, upper_units_inclusive, price | seeded with the REG electricity tariff; water prices are starting values for the admin to update from WASAC |

Usage is never stored. It is worked out from the readings (each reading minus the one before it), so editing or deleting a reading can never leave a wrong total behind.

## Robustness

- **Input checks everywhere:** menus re-ask until the answer is valid; Ctrl+C cancels the current action instead of crashing.
- **Meters only count up:** a reading must be at least the previous one and at most the next one; no future dates, no duplicate days, no absurd values.
- **Districts:** only Rwanda's 30 districts are accepted.
- **Security:** passwords are hashed with a salt; login gives the same error for a wrong username or password; 3 attempts per login; household accounts cannot reach other households.
- **Safe SQL:** every query uses `?` parameters, so typed text can never run as SQL.
- **Transactions:** every write commits fully or rolls back.
- **Logging:** logins, changes and unexpected errors are written to `homemeter.log`; the user sees a friendly message instead of a traceback.

## Team

| Member | Built |
|---|---|
| Bellamy | Project setup, models, database layer, permissions, demo data, documentation |
| Yanice | Input helpers and menu loop (`cli/prompts.py`), app routing (`cli/app.py`, `main.py`) |
| Iris | Households: repository, service, admin menu |
| Bruno | Accounts and login: password hashing, user repository, auth service, account menus |
| Pacifique | Meter readings: repository, validation service, readings menu |
| Vainqueur | Tariffs, cost reports and alerts: tariff repository, three services, reports menu |

## Sources

- Rwanda Energy Group. (2025). *Electricity access reaches 85.4%, up from 64.53% five years ago.* https://www.reg.rw/media-center/news-details/news/electricity-access-reaches-854-up-from-6453-five-years-ago-reg/
- Rwanda Energy Group. (2025). *Electricity tariffs effective from 1st October 2025.* https://www.reg.rw/customer-service/tariffs/
- Water and Sanitation Corporation. (n.d.). *Tariffs and charges.* https://www.wasac.rw/publications/tariffs-and-charges
