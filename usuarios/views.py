# Importações do Django
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.core.mail import send_mail
from django.core.paginator import Paginator
from urllib.parse import urlencode

# Importações locais
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .forms import PerfilForm, UsuarioLoginForm, UsuarioRegistroForm
from .models import LogAtividade, Perfil


def home(request):
    # Página inicial: se autenticado, ir ao dashboard; caso contrário, ir ao login
    if request.user.is_authenticated:
        return redirect("documentos:dashboard")
    return redirect("login")


def registro(request):
    if request.method == "POST":
        form = UsuarioRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get("username")
            messages.success(
                request,
                f"Conta criada para {username}! Aguarde a aprovação do administrador para receber o e-mail de ativação.",
            )

            # Notificar administradores sobre o novo registro
            enviar_email_notificacao_admin(request, user)

            # Registrar atividade
            registrar_atividade(
                request,
                "Registro de usuário",
                f"Usuário {username} se registrou no sistema",
                user,
            )

            return redirect("login")
    else:
        form = UsuarioRegistroForm()
    return render(request, "usuarios/registro.html", {"form": form})


@login_required
def aprovar_usuario(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    perfil_aprovacao = user.perfil

    if request.method == "POST":
        is_admin = request.POST.get("is_admin") == "on"
        user.is_staff = is_admin
        user.save()

        perfil_aprovacao.status = "aprovado"
        perfil_aprovacao.save()

        enviar_email_ativacao(request, user)

        registrar_atividade(
            request,
            "Aprovação de usuário",
            f"Administrador {request.user.username} aprovou o usuário {user.username} como {'administrador' if is_admin else 'usuário normal'}",
        )

        messages.success(
            request,
            f"O usuário <strong>{user.username}</strong> foi aprovado como <strong>{'administrador' if is_admin else 'usuário normal'}</strong> e o e-mail de ativação foi enviado!",
        )
        return redirect("listar_usuarios_pendentes")

    return render(request, "usuarios/confirmar_aprovacao.html", {"usuario": user})


def enviar_email_ativacao(request, usuario):
    token = str(uuid.uuid4())
    perfil_usuario = usuario.perfil
    perfil_usuario.token_ativacao = token
    perfil_usuario.data_token = timezone.now()  # Definir a data atual do token
    perfil_usuario.save()
    subject = "Ative sua conta no DocFinance"

    # Construir o link de ativação
    activation_link = f"{request.scheme}://{request.get_host()}/ativar/{token}/"

    # Renderizar o template do e-mail
    html_message = render_to_string(
        "usuarios/email_ativacao.html",
        {
            "user": usuario,
            "activation_link": activation_link,
        },
    )

    plain_message = strip_tags(html_message)

    # Enviar o e-mail
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [usuario.email],
        html_message=html_message,
        fail_silently=False,
    )


def ativar_conta(request, token):
    try:
        perfil_ativacao = Perfil.objects.get(token_ativacao=token)  # pylint: disable=no-member
        usuario = perfil_ativacao.usuario

        # Verificar se o token expirou (mais de 24 horas)
        if timezone.now() > perfil_ativacao.data_token + timedelta(hours=24):
            # Registrar tentativa de ativação com token expirado
            registrar_atividade(
                request,
                "Tentativa de ativação com token expirado",
                f"Usuário {usuario.username} tentou ativar a conta com um token expirado",
                usuario,
            )

            # Token expirado, não ativar a conta
            return render(
                request,
                "usuarios/token_expirado.html",
                {
                    "mensagem": "O link de ativação expirado. Por favor, solicite um novo link."
                },
            )

        # Token válido, ativar a conta
        usuario.is_active = True
        usuario.save()

        # Registrar ativação bem-sucedida
        registrar_atividade(
            request,
            "Ativação de conta",
            f"Usuário {usuario.username} ativou sua conta com sucesso",
            usuario,
        )

        perfil_ativacao.status = "aprovado"
        perfil_ativacao.token_ativacao = None
        perfil_ativacao.save()

        messages.success(
            request, "Sua conta foi ativada com sucesso! Agora você pode fazer login."
        )
        return redirect("login")
    except Perfil.DoesNotExist as exc:  # pylint: disable=no-member
        # Registrar tentativa de ativação com token inválido
        registrar_atividade(
            request,
            "Tentativa de ativação com token inválido",
            f"Tentativa de ativação com token inválido: {token}",
            None,
        )
        raise Http404("Token inválido") from exc


@login_required
def perfil(request):
    if request.method == "POST":
        perfil_form = PerfilForm(
            request.POST, request.FILES, instance=request.user.perfil
        )
        if perfil_form.is_valid():
            perfil_form.save()

            # Registrar atividade
            registrar_atividade(
                request,
                "Atualização de perfil",
                f"Usuário {request.user.username} atualizou seu perfil",
            )

            messages.success(request, "Seu perfil foi atualizado com sucesso!")
            return redirect("perfil")
    else:
        perfil_form = PerfilForm(instance=request.user.perfil)

    context = {"perfil_form": perfil_form}
    return render(request, "usuarios/perfil.html", context)


@login_required
def editar_perfil(request):
    perfil = request.user.perfil
    if request.method == "POST":
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            # Registrar edição de perfil
            registrar_atividade(
                request,
                "Edição de perfil",
                f"Usuário {request.user.username} editou dados do perfil",
            )
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("perfil")
    else:
        form = PerfilForm(instance=perfil)
    
    return render(request, "usuarios/editar_perfil.html", {"form": form})


@login_required
def listar_usuarios(request):
    # Verificar se o usuário é administrador
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("home")

    usuarios = User.objects.all().order_by("-date_joined")
    return render(request, "usuarios/listar_usuarios.html", {"usuarios": usuarios})


@login_required
def ativar_usuario(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()

    perfil_ativacao = user.perfil
    perfil_ativacao.status = "aprovado"
    perfil_ativacao.token_ativacao = None
    perfil_ativacao.save()

    messages.success(request, f"O usuário {user.username} foi ativado com sucesso!")
    return redirect("listar_usuarios")


@login_required
def desativar_usuario(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        return redirect("home")

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, "Você não pode desativar sua própria conta.")
        return redirect("listar_usuarios")

    if user.username == "admin" or user.is_superuser:
        messages.error(
            request,
            '<div class="admin-protection-alert"><i class="fas fa-shield-alt"></i> O superusuário admin não pode ser desativado. Esta é uma medida de segurança do sistema.</div>',
        )
        return redirect("listar_usuarios")

    user.is_active = False
    user.save()

    perfil_atual = user.perfil
    perfil_atual.status = "rejeitado"
    perfil_atual.save()

    registrar_atividade(
        request,
        "Desativação de usuário",
        f"Administrador {request.user.username} desativou o usuário {user.username}",
    )

    messages.success(request, f"O usuário {user.username} foi desativado com sucesso!")
    return redirect("listar_usuarios")


@login_required
def excluir_usuario(request, user_id):
    # Verificar se o usuário é administrador
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        return redirect("home")

    user = get_object_or_404(User, id=user_id)

    # Não permitir excluir a si mesmo
    if user == request.user:
        messages.error(request, "Você não pode excluir sua própria conta.")
        return redirect("listar_usuarios")

    # Não permitir excluir o superusuário admin
    if user.username == "admin" or user.is_superuser:
        messages.error(
            request,
            '<div class="admin-protection-alert"><i class="fas fa-shield-alt"></i> O superusuário admin não pode ser excluído. Esta é uma medida de segurança do sistema.</div>',
        )
        return redirect("listar_usuarios")

    # Armazenar o nome do usuário para a mensagem
    username = user.username

    # Registrar atividade antes de excluir o usuário
    registrar_atividade(
        request,
        "Exclusão de usuário",
        f"Administrador {request.user.username} excluiu o usuário {username}",
    )

    # Excluir o usuário
    user.delete()

    messages.success(
        request, f"O usuário <strong>{username}</strong> foi excluído com sucesso!"
    )
    return redirect("listar_usuarios")


@login_required
def listar_usuarios_pendentes(request):
    # Verificar se o usuário é administrador
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("home")

    # Obter todos os usuários com status pendente
    perfis_pendentes = Perfil.objects.filter(status="pendente")  # pylint: disable=no-member
    usuarios_pendentes = User.objects.filter(perfil__in=perfis_pendentes)

    return render(
        request,
        "usuarios/listar_usuarios_pendentes.html",
        {"usuarios": usuarios_pendentes},
    )


@login_required
def rejeitar_usuario(request, user_id):
    # Verificar se o usuário é administrador
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para realizar esta ação.")
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    # Remover esta linha redundante:
    # perfil = user.perfil

    # Atualizar o status para rejeitado
    perfil_atual = user.perfil
    perfil_atual.status = "rejeitado"
    perfil_atual.save()

    # Registrar atividade
    registrar_atividade(
        request,
        "Rejeição de usuário",
        f"Administrador {request.user.username} rejeitou o usuário {user.username}",
    )

    messages.success(
        request, f"O usuário <strong>{user.username}</strong> foi rejeitado!"
    )
    return redirect("listar_usuarios_pendentes")


def enviar_email_notificacao_admin(request, user):
    """Envia e-mail para todos os administradores quando um novo usuário se registra"""
    admins = User.objects.filter(is_staff=True)
    admin_emails = [admin.email for admin in admins if admin.email]

    if not admin_emails:
        return  # Não há administradores com e-mail cadastrado

    subject = "Novo usuário registrado no DocFinance"

    # Renderizar o template do e-mail
    html_message = render_to_string(
        "usuarios/email_notificacao_admin.html",
        {
            "user": user,
            "admin_url": f"{request.scheme}://{request.get_host()}/admin/",
            "pendentes_url": f"{request.scheme}://{request.get_host()}/usuarios/pendentes/",
        },
    )

    plain_message = strip_tags(html_message)

    # Enviar o e-mail
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        admin_emails,
        html_message=html_message,
        fail_silently=False,
    )


def registrar_atividade(request, acao, detalhes, usuario=None):
    """
    Registra uma atividade no sistema.

    Args:
        request: O objeto de requisição HTTP
        acao: A ação realizada (string)
        detalhes: Detalhes sobre a ação (string)
        usuario: O usuário que realizou a ação (User object, opcional)

    Returns:
        LogAtividade: O objeto de log criado
    """
    # Se o usuário não for fornecido, tenta obter do request
    if usuario is None and request.user.is_authenticated:
        usuario = request.user

    # Obter o endereço IP do cliente
    ip = get_client_ip(request)

    # Criar e salvar o log
    log = LogAtividade.objects.create(  # pylint: disable=no-member
        usuario=usuario, acao=acao, detalhes=detalhes, ip=ip
    )

    return log


def get_client_ip(request):
    """
    Obtém o endereço IP do cliente a partir do request.

    Args:
        request: O objeto de requisição HTTP

    Returns:
        string: O endereço IP do cliente
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class CustomLoginView(LoginView):
    form_class = UsuarioLoginForm
    template_name = "usuarios/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        # Registrar atividade de login bem-sucedido
        registrar_atividade(
            self.request,
            "Login",
            f"Usuário {self.request.user.username} fez login no sistema",
        )
        return response

    def form_invalid(self, form):
        # Obter o nome de usuário que tentou fazer login
        username = form.cleaned_data.get("username", "")

        # Tentar encontrar o usuário no banco de dados
        try:
            user = User.objects.get(username=username)

            # Verificar o status do usuário
            if not user.is_active:
                # Verificar se o usuário tem um perfil
                try:
                    perfil_usuario = user.perfil
                    status = perfil_usuario.status

                    # Registrar a tentativa de login com base no status
                    if status == "pendente":
                        mensagem = f"Usuário {username} tentou fazer login, mas está pendente de aprovação"
                    elif status == "rejeitado":
                        mensagem = (
                            f"Usuário {username} tentou fazer login, mas foi rejeitado"
                        )
                    else:
                        mensagem = (
                            f"Usuário {username} tentou fazer login, mas não está ativo"
                        )

                    registrar_atividade(
                        self.request, "Tentativa de login", mensagem, user
                    )
                except Perfil.DoesNotExist:  # pylint: disable=no-member
                    # Se o usuário não tem perfil, registrar uma mensagem genérica
                    registrar_atividade(
                        self.request,
                        "Tentativa de login",
                        f"Usuário {username} tentou fazer login, mas não está ativo",
                        user,
                    )
            else:
                # Usuário ativo, mas senha incorreta
                registrar_atividade(
                    self.request,
                    "Tentativa de login",
                    f"Usuário {username} tentou fazer login com senha incorreta",
                    user,
                )
        except User.DoesNotExist:  # pylint: disable=no-member
            # Usuário não existe
            if username:
                registrar_atividade(
                    self.request,
                    "Tentativa de login",
                    f"Tentativa de login com nome de usuário inexistente: {username}",
                )

        # Retornar a resposta padrão para formulário inválido
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    template_name = "usuarios/logout.html"

    def dispatch(self, request, *args, **kwargs):
        # Registrar atividade antes de fazer logout
        if request.user.is_authenticated:
            registrar_atividade(
                request,
                "Logout",
                f"Usuário {request.user.username} fez logout do sistema",
            )
        return super().dispatch(request, *args, **kwargs)


@login_required
def listar_logs(request):
    # Verificar se o usuário é administrador
    if not request.user.is_staff:
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect("home")

    logs = LogAtividade.objects.all().order_by("-data_hora")  # pylint: disable=no-member

    # Filtros
    tipo = request.GET.get("tipo")
    usuario_id = request.GET.get("usuario")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if tipo:
        logs = logs.filter(acao=tipo)

    if usuario_id:
        logs = logs.filter(usuario_id=usuario_id)

    if data_inicio:
        logs = logs.filter(data_hora__gte=data_inicio)

    if data_fim:
        logs = logs.filter(data_hora__lte=data_fim)

    # Tamanho de página dinâmico
    try:
        page_size = int(request.GET.get("page_size", 10))
    except ValueError:
        page_size = 10
    if page_size not in {10, 20, 50, 100}:
        page_size = 10

    # Paginação
    paginator = Paginator(logs, page_size)
    page = request.GET.get("page")
    logs_paginados = paginator.get_page(page)

    # Preservar filtros na paginação
    params = request.GET.copy()
    if "page" in params:
        params.pop("page")
    querystring = params.urlencode()

    # Intervalo de páginas mais intuitivo (janela em torno da atual)
    current = logs_paginados.number
    num_pages = paginator.num_pages
    start = max(1, current - 2)
    end = min(num_pages, current + 2)
    page_range = list(range(start, end + 1))
    show_first_ellipsis = start > 1
    show_last_ellipsis = end < num_pages

    context = {
        "logs": logs_paginados,
        "usuarios": User.objects.all(),
        "page_range": page_range,
        "show_first_ellipsis": show_first_ellipsis,
        "show_last_ellipsis": show_last_ellipsis,
        "querystring": querystring,
        "page_size": page_size,
        "page_size_options": [10, 20, 50, 100],
        "tipo": tipo,
        "usuario_id": usuario_id,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }

    return render(request, "usuarios/listar_logs.html", context)


class CustomPasswordResetView(PasswordResetView):
    template_name = "usuarios/password_reset.html"
    email_template_name = "usuarios/password_reset_email.html"
    subject_template_name = "usuarios/password_reset_subject.txt"

    def form_valid(self, form):
        # Obter o e-mail do formulário
        email = form.cleaned_data.get("email")

        # Tentar encontrar o usuário pelo e-mail
        try:
            user = User.objects.get(email=email)
            # Registrar atividade
            registrar_atividade(
                self.request,
                "Recuperação de senha",
                f"Solicitação de recuperação de senha para o e-mail {email}",
                user,
            )
        except User.DoesNotExist:  # pylint: disable=no-member
            # Se o usuário não existir, ainda registramos a tentativa
            registrar_atividade(
                self.request,
                "Recuperação de senha",
                f"Tentativa de recuperação de senha para e-mail não cadastrado: {email}",
            )

        return super().form_valid(form)

def teste_estatico(request):
    return render(request, "static_test.html")
