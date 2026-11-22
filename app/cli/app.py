import utils.transport
import utils.session
from app.cli import auth_menu, households_menu, readings_menu, reports_menu
from app.cli.prompts import Cancelled, header, run_action, run_menu
from app.database import Database
from app.models import User
from app.services.alert_service import AlertService
from app.services.auth_service import AuthService
from app.services.household_service import HouseholdService
from app.services.reading_service import ReadingService
from app.services.report_service import ReportService
from app.services.tariff_service import TariffService


class App:
    """Builds every service once and routes each user to the menu for their role."""

    def __init__(self, db: Database):
        self.auth = AuthService(db)
        self.households = HouseholdService(db)
        self.readings = ReadingService(db)
        self.tariffs = TariffService(db)
        self.reports = ReportService(self.households, self.readings, self.tariffs)
        self.alerts = AlertService(self.readings, self.tariffs)

    def run(self) -> None:
        if self.auth.needs_setup():
            run_action(lambda: auth_menu.first_run_setup(self.auth), pause_after=False)
        run_menu("WELCOME TO HOMEMETER", [("Log in", self._log_in)],
                 subtitle="Household energy & water monitor", exit_label="Exit program", pause_after=False)
        print("\nGoodbye! Keep saving energy and water.")

    def _log_in(self) -> None:
        user = auth_menu.login(self.auth)
        if user.is_admin:
            self._admin_menu(user)
        else:
            self._household_menu(user)

    def _household_menu(self, user: User) -> None:
        household = self.households.get(user, user.household_id)
        self._household_actions(user, household.id, f"{household.name} ({household.district})", "Log out")

    def _household_actions(self, user: User, household_id: str, subtitle: str, exit_label: str) -> None:
        options = [
            ("Record a meter reading", lambda: readings_menu.record_reading(user, household_id, self.readings)),
            ("View monthly usage & cost report", lambda: reports_menu.monthly_report(user, household_id, self.reports)),
            ("Check usage alerts & saving tips", lambda: reports_menu.alerts_and_tips(user, household_id, self.alerts)),
            ("Manage my readings (view / edit / delete)",
             lambda: readings_menu.manage_readings(user, household_id, self.readings)),
            ("View usage history (6 months)", lambda: reports_menu.usage_history(user, household_id, self.reports)),
        ]
        if not user.is_admin:
            options.append(("Change my password", lambda: auth_menu.change_password(user, self.auth)))
        run_menu("HOMEMETER: HOUSEHOLD MENU", options, subtitle=subtitle, exit_label=exit_label)

    def _admin_menu(self, user: User) -> None:
        run_menu("HOMEMETER: ADMIN MENU", [
            ("Manage households", lambda: households_menu.manage_households(user, self.households)),
            ("Manage user accounts", lambda: auth_menu.manage_users(user, self.auth, self.households)),
            ("Manage tariffs", lambda: reports_menu.manage_tariffs(user, self.tariffs)),
            ("Open a household (readings & reports)", lambda: self._open_household(user)),
            ("All households overview", lambda: reports_menu.households_overview(user, self.reports)),
            ("Change my password", lambda: auth_menu.change_password(user, self.auth)),
        ], subtitle=f"Logged in as {user.username} (admin)", exit_label="Log out")

    def _open_household(self, user: User) -> None:
        header("OPEN A HOUSEHOLD")
        household = households_menu.choose_household(user, self.households)
        self._household_actions(user, household.id, f"{household.name} ({household.district}) - admin view",
                                "Back to admin menu")
