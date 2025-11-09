import logging
import threading

from django.urls import resolve

from .views import registrar_atividade

# Thread-local para disponibilizar o usuário/IP atual aos signals
thread_local = threading.local()

logger = logging.getLogger(__name__)


class LogAtividadeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Disponibilizar usuário e IP em thread-local
        try:
            thread_local.current_user = request.user if request.user.is_authenticated else None
            # Capturar IP (básico)
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
            thread_local.current_ip = ip
        except Exception:
            thread_local.current_user = None
            thread_local.current_ip = None

        response = self.get_response(request)

        # Não registrar atividades para requisições de arquivos estáticos ou admin
        if request.path.startswith("/static/") or request.path.startswith("/admin/"):
            return response

        # Registrar apenas para usuários autenticados
        if request.user.is_authenticated:
            try:
                resolver_match = resolve(request.path)
                view_name = resolver_match.url_name

                # Não registrar atividades para certas views
                if view_name not in ["listar_logs", "static"]:
                    metodo = request.method.upper()

                    # Acesso (GET) e ações (POST/PUT/PATCH/DELETE)
                    if metodo == "GET":
                        registrar_atividade(
                            request,
                            f"Acesso à página: {view_name}",
                            f"Usuário acessou a página {request.path}",
                        )
                    elif metodo in {"POST", "PUT", "PATCH", "DELETE"}:
                        registrar_atividade(
                            request,
                            f"Ação {metodo} na página: {view_name}",
                            f"Usuário realizou {metodo} em {request.path}",
                        )
            except Exception:
                pass  # Ignorar erros de resolução de URL

        return response
