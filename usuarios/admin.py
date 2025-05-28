from django.contrib import admin

from .models import LogAtividade, Perfil


class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "telefone", "matricula", "cpf", "status")
    list_filter = ("status",)
    search_fields = ("usuario__username", "usuario__email", "matricula", "cpf")


admin.site.register(Perfil, PerfilAdmin)


class LogAtividadeAdmin(admin.ModelAdmin):
    list_display = ("usuario", "acao", "data_hora", "ip")
    list_filter = ("acao", "data_hora", "usuario")
    search_fields = ("usuario__username", "detalhes", "ip")
    readonly_fields = ("usuario", "acao", "detalhes", "data_hora", "ip")


admin.site.register(LogAtividade, LogAtividadeAdmin)
