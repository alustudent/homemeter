# HomeMeter: Household Energy & Water Monitor

A menu-driven command-line app that helps Rwandan households record their electricity and water meter readings, see what they used and what it cost under the block tariffs, and get warned before their usage jumps into a more expensive block.

Built by Team 6 (BSE Year 1, Cohort 1) for Peer Learning Project 2. GCGOs: Climate Change, Infrastructure, Natural Resource Management.

## Status

This commit sets up the project base: settings, data classes, errors, permission checks and the SQLite database layer. Each team member adds one feature on top of it.

## Run the tests

Requires **Python 3.11 or newer**. Only the standard library is used.

```bash
python3 -m unittest -v
```

## Layout

```
app/
  config.py        settings, default tariffs, districts, saving tips
  models.py        User, Household, MeterReading, TariffBlock, UsageLine, Role, Utility
  errors.py        errors whose messages are safe to show the user
  permissions.py   require_admin, require_household_access
  database.py      SQLite schema, default tariffs, transactions
  repositories/    SQL for each table (added per feature)
  services/        rules and calculations (added per feature)
  cli/             terminal menus (added per feature)
tests/
```
