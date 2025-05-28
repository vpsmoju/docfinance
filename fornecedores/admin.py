from django.contrib import admin

from .models import Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "cnpj_cpf", "telefone", "email")
    list_filter = ("tipo",)
    search_fields = ("nome", "cnpj_cpf", "email")
    ordering = ("nome",)


# Register your models here.
