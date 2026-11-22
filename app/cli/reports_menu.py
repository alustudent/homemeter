from datetime import date

from app.cli.prompts import ask_float, ask_month, choose, header, money, print_table, run_menu, success, warn
from app.models import UsageLine, User, Utility
from app.services.alert_service import AlertService
from app.services.reading_service import month_key
from app.services.report_service import ReportService
from app.services.tariff_service import TariffService


def _change(line: UsageLine) -> str:
    return "-" if line.change is None else f"{line.change:+.0%}"


def monthly_report(actor: User, household_id: str, reports: ReportService) -> None:
    month = ask_month("Which month?", month_key(date.today()))
    header(f"USAGE AND COST REPORT: {month}")
    lines = reports.monthly(actor, household_id, month)
    rows = [(l.utility.label, f"{l.units:g} {l.utility.unit}", money(l.cost), _change(l)) for l in lines]
    print_table(["Utility", "Used", "Estimated cost", "vs last month"], rows)
    print(f"\nTotal estimated cost: {money(sum(l.cost for l in lines))}")


def usage_history(actor: User, household_id: str, reports: ReportService) -> None:
    month = month_key(date.today())
    header("USAGE HISTORY (LAST 6 MONTHS)")
    rows = []
    for m, lines in reports.history(actor, household_id, month):
        power, water = lines
        rows.append((m, f"{power.units:g}", money(power.cost), f"{water.units:g}", money(water.cost),
                     money(power.cost + water.cost)))
    print_table(["Month", "kWh", "Power cost", "m3", "Water cost", "Total"], rows)


def alerts_and_tips(actor: User, household_id: str, alerts: AlertService) -> None:
    header("USAGE ALERTS AND SAVING TIPS")
    found = alerts.check(actor, household_id)
    if not found:
        success("No alerts. Your usage looks normal this month.")
    for alert in found:
        warn(f"{alert.utility.label}: {alert.message}")
    for utility in sorted({a.utility for a in found}, key=list(Utility).index) or list(Utility):
        print(f"\n{utility.label} saving tips:")
        for tip in alerts.tips(utility):
            print(f" - {tip}")


def show_tariffs(tariffs: TariffService) -> None:
    header("CURRENT TARIFFS (RWF PER UNIT)")
    rows = [(u.label, f"{b.label} {u.unit}", f"{b.price:g}") for u in Utility for b in tariffs.list_for(u)]
    print_table(["Utility", "Monthly block", "Price"], rows)


def edit_tariff(actor: User, tariffs: TariffService) -> None:
    header("CHANGE A TARIFF PRICE")
    blocks = [b for u in Utility for b in tariffs.list_for(u)]
    block = blocks[choose("Choose a block", [f"{b.utility.label} {b.label} {b.utility.unit}: {b.price:g} RWF"
                                             for b in blocks])]
    updated = tariffs.update_price(actor, block.id, ask_float("New price in RWF per unit", block.price))
    success(f"{updated.utility.label} {updated.label} now costs {updated.price:g} RWF per {updated.utility.unit}.")


def households_overview(actor: User, reports: ReportService) -> None:
    month = ask_month("Which month?", month_key(date.today()))
    header(f"ALL HOUSEHOLDS: {month}")
    rows = []
    for household, (power, water) in reports.overview(actor, month):
        rows.append((household.name, household.district, f"{power.units:g}", f"{water.units:g}",
                     money(power.cost + water.cost)))
    print_table(["Household", "District", "kWh", "m3", "Total cost"], rows)


def manage_tariffs(actor: User, tariffs: TariffService) -> None:
    run_menu("MANAGE TARIFFS", [
        ("View tariffs", lambda: show_tariffs(tariffs)),
        ("Change a price", lambda: edit_tariff(actor, tariffs)),
    ])
