from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("registro/", views.registro, name="registro"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("perfil/", views.perfil, name="perfil"),
    path("perfil/editar/", views.editar_perfil, name="editar_perfil"),
    path("ativar/<str:token>/", views.ativar_conta, name="ativar_conta"),
    # Rotas de administração de usuários
    path("usuarios/", views.listar_usuarios, name="listar_usuarios"),
    path(
        "usuarios/pendentes/",
        views.listar_usuarios_pendentes,
        name="listar_usuarios_pendentes",
    ),
    path(
        "usuarios/aprovar/<int:user_id>/", views.aprovar_usuario, name="aprovar_usuario"
    ),
    path(
        "usuarios/rejeitar/<int:user_id>/",
        views.rejeitar_usuario,
        name="rejeitar_usuario",
    ),
    path("usuarios/ativar/<int:user_id>/", views.ativar_usuario, name="ativar_usuario"),
    path(
        "usuarios/desativar/<int:user_id>/",
        views.desativar_usuario,
        name="desativar_usuario",
    ),
    path(
        "usuarios/excluir/<int:user_id>/", views.excluir_usuario, name="excluir_usuario"
    ),
    # Logs de atividade
    path("logs/", views.listar_logs, name="listar_logs"),
    # Rotas de redefinição de senha
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="usuarios/password_reset.html",
            email_template_name="usuarios/password_reset_email.html",
            subject_template_name="usuarios/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="usuarios/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="usuarios/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="usuarios/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
