import logging

from django.urls import resolve

from .views import registrar_atividade

logger = logging.getLogger(__name__)


class LogAtividadeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Não registrar atividades para requisições de arquivos estáticos ou admin
        if request.path.startswith("/static/") or request.path.startswith("/admin/"):
            return response

        # Registrar apenas para usuários autenticados
        if request.user.is_authenticated:
            # Obter o nome da view atual
            try:
                resolver_match = resolve(request.path)
                view_name = resolver_match.url_name

                # Não registrar atividades para certas views
                if view_name not in ["listar_logs", "static"]:
                    registrar_atividade(
                        request,
                        f"Acesso à página: {view_name}",
                        f"Usuário acessou a página {request.path}",
                    )
            except Exception:
                pass  # Ignorar erros de resolução de URL

        return response
