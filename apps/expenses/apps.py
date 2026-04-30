from django.apps import AppConfig


class ExpensesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.expenses"
    label = "expenses"
    verbose_name = "Expenses"

    def ready(self) -> None:  # noqa: D401
        from . import signals  # noqa: F401
