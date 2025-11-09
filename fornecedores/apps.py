from django.apps import AppConfig


class FornecedoresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fornecedores"
    verbose_name = "Fornecedores"

    def ready(self):
        # Importa os signals para ativá-los
        from . import signals  # noqa: F401
