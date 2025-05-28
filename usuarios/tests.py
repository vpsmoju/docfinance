# from django.db import transaction # Removido - @transaction.atomic não será mais usado
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core import mail
from django.test import (
    TestCase,
    TransactionTestCase,  # Mudar para TransactionTestCase
)
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from usuarios.forms import UsuarioRegistroForm
from usuarios.models import LogAtividade, Perfil


# Testes para modelos
class PerfilCriacaoTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        User.objects.all().delete()
        Perfil.objects.all().delete()

    def test_perfil_criacao(self):
        username = f"user_criacao_{uuid.uuid4().hex[:8]}"
        usuario = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpassword123",
        )
        # Deletar perfil existente se houver
        Perfil.objects.filter(usuario=usuario).delete()

        cpf_uuid_part = uuid.uuid4().hex
        perfil = Perfil.objects.create(
            usuario=usuario,
            telefone="(91) 98765-4321",
            matricula="12345",
            cpf=f"{cpf_uuid_part[:3]}.{cpf_uuid_part[3:6]}.{cpf_uuid_part[6:9]}-{cpf_uuid_part[9:11]}",
            status="pendente",
        )
        self.assertEqual(perfil.usuario.username, usuario.username)
        self.assertEqual(perfil.telefone, "(91) 98765-4321")
        self.assertEqual(perfil.matricula, "12345")
        self.assertEqual(
            perfil.cpf,
            f"{cpf_uuid_part[:3]}.{cpf_uuid_part[3:6]}.{cpf_uuid_part[6:9]}-{cpf_uuid_part[9:11]}",
        )
        self.assertEqual(perfil.status, "pendente")


class PerfilStrTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        User.objects.all().delete()
        Perfil.objects.all().delete()

    def test_perfil_str(self):
        username = f"user_str_{uuid.uuid4().hex[:8]}"
        usuario = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpassword123",
        )
        # Deletar perfil existente se houver
        Perfil.objects.filter(usuario=usuario).delete()

        cpf_uuid_part = uuid.uuid4().hex
        perfil = Perfil.objects.create(
            usuario=usuario,
            telefone="(91) 11111-1111",
            matricula="STR123",
            cpf=f"{cpf_uuid_part[:3]}.{cpf_uuid_part[3:6]}.{cpf_uuid_part[6:9]}-{cpf_uuid_part[9:11]}",
            status="pendente",
        )
        self.assertEqual(str(perfil), f"Perfil de {usuario.username}")


class PerfilStatusTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        User.objects.all().delete()
        Perfil.objects.all().delete()

    def test_perfil_status_choices(self):
        username = f"user_status_{uuid.uuid4().hex[:8]}"
        usuario = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpassword123",
        )
        # Deletar perfil existente se houver
        Perfil.objects.filter(usuario=usuario).delete()

        cpf_uuid_part = uuid.uuid4().hex
        perfil = Perfil.objects.create(
            usuario=usuario,
            telefone="(91) 22222-2222",
            matricula="STATUS123",
            cpf=f"{cpf_uuid_part[:3]}.{cpf_uuid_part[3:6]}.{cpf_uuid_part[6:9]}-{cpf_uuid_part[9:11]}",
            status="pendente",
        )
        self.assertEqual(perfil.status, "pendente")
        perfil.status = "aprovado"
        perfil.save()
        self.assertEqual(perfil.status, "aprovado")
        perfil.status = "rejeitado"
        perfil.save()
        self.assertEqual(perfil.status, "rejeitado")


class LogAtividadeTest(TestCase):
    """Testes para o modelo LogAtividade"""

    def setUp(self):
        """Configuração inicial para o teste"""
        self.username = f"log_user_{uuid.uuid4().hex[:8]}"
        self.usuario = User.objects.create_user(
            username=self.username,
            email=f"{self.username}@example.com",
            password="testpassword123",
        )

    # @transaction.atomic # Removido
    def test_log_criacao(self):
        """Testa se o log foi criado corretamente"""
        log = LogAtividade.objects.create(
            usuario=self.usuario,
            acao="Login",
            detalhes="Usuário fez login no sistema",
            ip="127.0.0.1",
        )

        self.assertEqual(log.usuario.username, self.usuario.username)
        self.assertEqual(log.acao, "Login")
        self.assertEqual(log.detalhes, "Usuário fez login no sistema")
        self.assertEqual(log.ip, "127.0.0.1")
        self.assertLessEqual((timezone.now() - log.data_hora).total_seconds(), 10)

    # @transaction.atomic # Removido
    def test_log_str(self):
        """Testa a representação string do log"""
        log = LogAtividade.objects.create(
            usuario=self.usuario,
            acao="Login",
            detalhes="Usuário fez login no sistema",
            ip="127.0.0.1",
        )

        expected_format = f"{self.usuario.username} - Login - {log.data_hora}"
        self.assertEqual(str(log), expected_format)


class UsuarioRegistroFormTest(TestCase):
    """Testes para o formulário de registro de usuário"""

    def setUp(self):
        """Configuração inicial para o teste"""
        # Usar o UUID completo para evitar problemas com fatiamento
        self.unique_id_full = uuid.uuid4().hex

    # @transaction.atomic # Removido
    def test_registro_form_valido(self):
        """Testa se o formulário de registro é válido com dados corretos"""
        form_data = {
            "username": f"form_valido_{self.unique_id_full[:8]}",
            "email": f"form_valido_{self.unique_id_full[:8]}@example.com",
            "password1": "senhaSegura123",
            "password2": "senhaSegura123",
            "first_name": "Novo",
            "last_name": "Usuário",
            "telefone": f"(91) 9{self.unique_id_full[10:14]}-{self.unique_id_full[14:18]}",  # Usar fatias diferentes para telefone
            "matricula": f"MAT{self.unique_id_full[:8]}",
            # Usar fatias do unique_id_full para garantir comprimento suficiente para o CPF
            "cpf": f"{self.unique_id_full[:3]}.{self.unique_id_full[3:6]}.{self.unique_id_full[6:9]}-{self.unique_id_full[9:11]}",
        }
        form = UsuarioRegistroForm(data=form_data)
        if (
            not form.is_valid()
        ):  # Adicionado para depuração, caso o form não seja válido
            print(
                f"Formulário inválido em test_registro_form_valido: {form.errors.as_json()}"
            )
        self.assertTrue(form.is_valid())

    # @transaction.atomic # Removido
    def test_registro_form_senhas_diferentes(self):
        """Testa se o formulário é inválido quando as senhas não coincidem"""
        form_data = {
            "username": f"form_invalido_{self.unique_id_full[:8]}",
            "email": f"form_invalido_{self.unique_id_full[:8]}@example.com",
            "password1": "senhaSegura123",
            "password2": "senhaSegura456",
            "first_name": "Novo",
            "last_name": "Usuário",
            "telefone": f"(91) 9{self.unique_id_full[10:14]}-{self.unique_id_full[14:18]}",
            "matricula": f"MAT{self.unique_id_full[:8]}",
            "cpf": f"{self.unique_id_full[:3]}.{self.unique_id_full[3:6]}.{self.unique_id_full[6:9]}-{self.unique_id_full[9:11]}",
        }
        form = UsuarioRegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class RegistroViewTest(TestCase):
    """Testes para a view de registro de usuário"""

    def setUp(self):
        """Configuração inicial para o teste"""
        self.client = self.client_class()
        self.registro_url = reverse("registro")

    def test_registro_view_get(self):
        """Testa se a página de registro é carregada corretamente"""
        response = self.client.get(self.registro_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "usuarios/registro.html")


class AtivacaoContaTest(TestCase):
    """Testes para o processo de ativação de conta"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.username = f"ativacao_user_{uuid.uuid4().hex[:8]}"
        self.user = User.objects.create_user(
            username=self.username,
            email=f"{self.username}@example.com",
            password="testpassword123",
            is_active=False,
        )
        self.perfil = self.user.perfil
        self.perfil.token_ativacao = str(uuid.uuid4())
        self.perfil.status = "pendente"
        self.perfil.save()

    def test_token_valido_ativa_conta(self):
        """Testa se um token válido ativa a conta corretamente"""
        # Definir data do token para 1 hora atrás (dentro do prazo)
        self.perfil.data_token = timezone.now() - timedelta(hours=1)
        self.perfil.save()

        # Tentar ativar com token válido
        response = self.client.get(
            reverse("ativar_conta", args=[self.perfil.token_ativacao]), follow=True
        )
        # Adicionar uma verificação usando a resposta
        self.assertEqual(response.status_code, 200)

        # Verificar se a conta foi ativada
        self.user.refresh_from_db()
        self.perfil.refresh_from_db()

        # Verificações de estado
        self.assertTrue(self.user.is_active)  # Usuário deve estar ativo
        self.assertEqual(self.perfil.status, "aprovado")  # Status deve ser aprovado
        self.assertIsNone(self.perfil.token_ativacao)  # Token deve ser limpo

        # Verificar se foi redirecionado para a página de login
        self.assertRedirects(response, reverse("login"))

        # Verificar se há mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("sucesso" in str(message).lower() for message in messages))

        # Verificar se um log de ativação foi criado
        ultimo_log = LogAtividade.objects.latest("data_hora")
        self.assertEqual(ultimo_log.usuario, self.user)
        self.assertEqual(ultimo_log.acao, "Ativação de conta")

        def test_ativacao_token_invalido(self):
            """Testa se a ativação falha com token inválido"""
            response = self.client.get(reverse("ativar_conta", args=["token_invalido"]))
            self.assertEqual(response.status_code, 404)


class PermissoesAdminTest(TestCase):
    """Testes para permissões de administrador"""

    def setUp(self):
        """Configuração inicial para os testes"""
        # Criar usuário admin
        self.admin_username = f"admin_user_{uuid.uuid4().hex[:8]}"
        self.admin_user = User.objects.create_user(
            username=self.admin_username,
            email=f"{self.admin_username}@example.com",
            password="adminpass123",
            is_staff=True,
            is_active=True,
        )
        self.admin_user.perfil.status = "aprovado"
        self.admin_user.perfil.save()

        # Criar usuário normal pendente
        self.user_username = f"normal_user_{uuid.uuid4().hex[:8]}"
        self.normal_user = User.objects.create_user(
            username=self.user_username,
            email=f"{self.user_username}@example.com",
            password="userpass123",
            is_active=False,
        )
        self.normal_user.perfil.status = "pendente"
        self.normal_user.perfil.save()

    def test_aprovacao_usuario_por_admin(self):
        """Testa se um admin pode aprovar um usuário"""
        self.client.login(username=self.admin_username, password="adminpass123")

        response = self.client.post(
            reverse("aprovar_usuario", args=[self.normal_user.id]),
            {"is_admin": "on"},  # Aprovar como admin
        )

        # Recarregar o usuário do banco de dados
        self.normal_user.refresh_from_db()
        self.normal_user.perfil.refresh_from_db()

        self.assertEqual(response.status_code, 302)  # Redirecionamento
        self.assertTrue(self.normal_user.is_staff)  # Verificar se é admin
        self.assertEqual(self.normal_user.perfil.status, "aprovado")

    def test_aprovacao_negada_para_nao_admin(self):
        """Testa se um usuário não-admin não pode aprovar outros usuários"""
        # Criar um usuário não-admin
        non_admin = User.objects.create_user(
            username=f"non_admin_{uuid.uuid4().hex[:8]}",
            email="nonadmin@example.com",
            password="nonadmin123",
            is_active=True,
        )
        self.client.login(username=non_admin.username, password="nonadmin123")

        response = self.client.post(
            reverse("aprovar_usuario", args=[self.normal_user.id]), {"is_admin": "off"}
        )

        self.assertEqual(response.status_code, 302)  # Redirecionamento para home
        self.assertFalse(self.normal_user.is_staff)  # Não deve ter sido alterado
        self.assertEqual(self.normal_user.perfil.status, "pendente")


class EmailTest(TestCase):
    """Testes para funcionalidades de e-mail"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.username = f"email_user_{uuid.uuid4().hex[:8]}"
        self.user = User.objects.create_user(
            username=self.username,
            email=f"{self.username}@example.com",
            password="testpassword123",
            is_active=False,
        )
        self.perfil = self.user.perfil
        self.perfil.token_ativacao = str(uuid.uuid4())
        self.perfil.status = "pendente"
        self.perfil.save()

        # Criar um admin para testar notificações
        self.admin = User.objects.create_user(
            username=f"admin_{uuid.uuid4().hex[:8]}",
            email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
            password="adminpass123",
            is_staff=True,
        )

    def test_envio_email_ativacao(self):
        """Testa se o e-mail de ativação é enviado corretamente"""
        mail.outbox = []

        # Criar dados do usuário com UUID único
        unique_id = uuid.uuid4().hex
        test_email = "novo@example.com"

        # Criar o usuário diretamente
        user = User.objects.create_user(
            username=f"novo_user_{unique_id[:8]}",
            email=test_email,
            password="senhaSegura123",
            is_active=False,
        )

        # O perfil já foi criado automaticamente pelo signal, apenas atualizá-lo
        perfil = user.perfil
        perfil.telefone = "(91) 98765-4321"
        perfil.matricula = f"MAT{unique_id[:8]}"
        perfil.cpf = (
            f"{unique_id[:3]}.{unique_id[3:6]}.{unique_id[6:9]}-{unique_id[9:11]}"
        )
        perfil.save()

        # Enviar e-mail de ativação
        from usuarios.views import enviar_email_ativacao

        enviar_email_ativacao(self.client.request().wsgi_request, user)

        # Verificações atualizadas para corresponder ao assunto real do e-mail
        self.assertEqual(len(mail.outbox), 1)
        email_enviado = mail.outbox[0]
        self.assertEqual(email_enviado.to[0], test_email)
        self.assertEqual(email_enviado.subject, "Ative sua conta no DocFinance")
        self.assertIn("ativar sua conta", email_enviado.body)


class SegurancaTest(TestCase):
    """Testes de segurança do sistema"""

    def setUp(self):
        """Configuração inicial para os testes"""
        self.username = f"security_user_{uuid.uuid4().hex[:8]}"
        self.user = User.objects.create_user(
            username=self.username,
            email=f"{self.username}@example.com",
            password="testpassword123",
            is_active=False,
        )
        self.perfil = self.user.perfil
        self.perfil.token_ativacao = str(uuid.uuid4())
        self.perfil.data_token = timezone.now()
        self.perfil.status = "pendente"
        self.perfil.save()

    def test_token_expirado(self):
        """Testa se tokens expirados são rejeitados"""
        # Definir data do token para 48 horas atrás
        self.perfil.data_token = timezone.now() - timedelta(hours=48)
        self.perfil.save()

        # Guardar o estado inicial para comparação
        _is_active_antes = self.user.is_active
        _status_antes = self.perfil.status
        _token_antes = self.perfil.token_ativacao

        # Tentar ativar com token expirado
        response = self.client.get(
            reverse("ativar_conta", args=[self.perfil.token_ativacao]), follow=True
        )

        # Verificar se a resposta final após redirecionamento é a página de erro
        self.assertEqual(response.status_code, 200)

        # Verificar se a conta permanece inativa
        self.user.refresh_from_db()
        self.perfil.refresh_from_db()

        # Verificações de estado
        self.assertFalse(self.user.is_active)  # Usuário deve permanecer inativo
        self.assertEqual(
            self.perfil.status, "pendente"
        )  # Status deve continuar pendente
        self.assertIsNotNone(self.perfil.token_ativacao)  # Token não deve ser limpo

        # Verificar se o template correto foi usado
        self.assertTemplateUsed(response, "usuarios/token_expirado.html")

        # Verificar se há mensagem de erro na resposta
        self.assertContains(response, "expirado", status_code=200)

    def test_token_expirado_cria_log(self):
        """Testa se tentativas de ativação com token expirado são registradas no log"""
        # Definir data do token para 48 horas atrás
        self.perfil.data_token = timezone.now() - timedelta(hours=48)
        self.perfil.save()

        # Guardar o estado inicial para comparação
        logs_antes = LogAtividade.objects.count()

        # Tentar ativar com token expirado
        self.client.get(
            reverse("ativar_conta", args=[self.perfil.token_ativacao]), follow=True
        )

        # Verificar se um novo log foi criado
        logs_depois = LogAtividade.objects.count()
        self.assertEqual(logs_depois, logs_antes + 1)

        # Verificar se o log contém as informações corretas
        ultimo_log = LogAtividade.objects.latest("data_hora")
        self.assertEqual(ultimo_log.usuario, self.user)
        self.assertEqual(ultimo_log.acao, "Tentativa de ativação com token expirado")
        self.assertIn(self.user.username, ultimo_log.detalhes)
        self.assertIn("token expirado", ultimo_log.detalhes.lower())


def test_protecao_rotas_admin(self):
    """Testa se rotas administrativas estão protegidas contra acesso não autorizado"""
    # Criar um usuário normal (não admin)
    User.objects.create_user(
        username="usuario_normal",
        email="normal@example.com",
        password="senha123",
        is_active=True,
    )

    # Fazer login como usuário normal
    self.client.login(username="usuario_normal", password="senha123")

    # Tentar acessar rotas administrativas
    rotas_admin = [
        reverse("listar_usuarios"),
        reverse("listar_usuarios_pendentes"),
        reverse("listar_logs"),
    ]

    for rota in rotas_admin:
        response = self.client.get(rota, follow=True)

        # Verificar se foi redirecionado para home
        self.assertRedirects(response, reverse("home"))

        # Verificar se há mensagem de erro
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("permissão" in str(message).lower() for message in messages)
        )


class RateLimitingTest(TestCase):
    def setUp(self):
        """Configuração inicial para os testes"""
        self.client = Client()
        self.num_tentativas = (
            5  # Aumentado para 5 para corresponder ao assertGreaterEqual
        )

        # Criar um usuário para testes
        self.username = f"rate_user_{uuid.uuid4().hex[:8]}"
        self.user = User.objects.create_user(
            username=self.username,
            email=f"{self.username}@example.com",
            password="testpassword123",
            is_active=True,
        )

    def test_login_tentativas_registradas(self):
        """Testa se o sistema registra tentativas de login"""
        self.num_tentativas = 3  # Definir número de tentativas como atributo da classe

        # Fazer várias tentativas de login com senha incorreta
        for _ in range(self.num_tentativas):  # Usar self.num_tentativas
            self.client.post(
                reverse("login"),
                {"username": self.username, "password": "senha_errada"},
            )

        # Verificar se pelo menos um log foi registrado
        logs = LogAtividade.objects.filter(usuario=self.user, acao="Tentativa de login")

        # Verificar se pelo menos uma tentativa foi registrada
        self.assertGreaterEqual(logs.count(), 1)

    def test_registro_multiplas_tentativas(self):
        """Testa se o sistema permite múltiplos registros"""
        self.num_tentativas = 3  # Definir número de tentativas como atributo da classe

        # Fazer várias tentativas de registro com dados diferentes
        for _ in range(self.num_tentativas):  # Usar self.num_tentativas
            unique_id = uuid.uuid4().hex
            self.client.post(
                reverse("registro"),
                {
                    "username": f"new_user_{unique_id[:8]}",
                    "email": f"new_{unique_id[:8]}@example.com",
                    "password1": "senhaSegura123",
                    "password2": "senhaSegura123",
                    "first_name": "Novo",
                    "last_name": "Usuário",
                    "telefone": f"(91) 9{unique_id[10:14]}-{unique_id[14:18]}",
                    "matricula": f"MAT{unique_id[:8]}",
                    "cpf": f"{unique_id[:3]}.{unique_id[3:6]}.{unique_id[6:9]}-{unique_id[9:11]}",
                },
            )

        # Verificar se pelo menos um usuário foi criado
        # (isso é apenas para verificar se o sistema permite registros)
        novos_usuarios = User.objects.filter(username__startswith="new_user_")
        self.assertGreaterEqual(novos_usuarios.count(), 1)

    def test_login_tentativas_excessivas(self):
        """Testa se o sistema registra múltiplas tentativas de login"""
        for i in range(
            self.num_tentativas
        ):  # Usar i como variável de loop e self.num_tentativas
            self.client.post(
                reverse("login"),
                {"username": self.username, "password": f"senha_errada_{i}"},
            )

        # Verificar se os logs foram registrados
        logs = LogAtividade.objects.filter(usuario=self.user, acao="Tentativa de login")

        # Verificar se várias tentativas foram registradas
        self.assertGreaterEqual(logs.count(), 5)
