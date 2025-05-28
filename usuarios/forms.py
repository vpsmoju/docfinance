"""
Módulo de formulários para registro de usuários, autenticação e gerenciamento de perfis.
Contém formulários para registro de usuários (UsuarioRegistroForm), login (UsuarioLoginForm)
e edição de perfis (PerfilForm).
"""

import uuid

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from .models import Perfil


class UsuarioRegistroForm(UserCreationForm):
    """
    Formulário para registro de usuários que estende o UserCreationForm do Django.
    Adiciona campos obrigatórios para email, nome e sobrenome.
    Cria uma conta de usuário inativa que requer verificação por email.
    """

    def get_fields(self):
        """Retorna os fields definidos nos form"""
        return self.fields

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")

    class Meta:
        """
        Classe Meta para UsuarioRegistroForm.
        Especifica User como modelo e define quais campos devem ser incluídos no formulário.
        """

        def get_fields(self):
            """Returns the fields defined in the Meta class"""
            return self.fields

        def get_model(self):
            """Returns the model defined in the Meta class"""
            return self.model

        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        """
        Salva o formulário de registro do usuário e cria uma conta de usuário inativa.

        Cria um novo usuário com o e-mail, nome e sobrenome fornecidos.
        A conta é definida como inativa até a verificação do e-mail.
        Gera um token de ativação para verificação do e-mail se o commit for True.

        Args:
            commit (bool): Se o usuário deve ser salvo no banco de dados. O padrão é True.

        Returns:
            User: A instância do usuário recém-criada.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_active = False  # Usuário inativo até aprovação

        if commit:
            user.save()
            # Gerar token de ativação
            perfil = user.perfil
            perfil.token_ativacao = str(uuid.uuid4())
            perfil.save()

        return user


class UsuarioLoginForm(AuthenticationForm):
    """
    Formulário para autenticação de usuários que estende o AuthenticationForm do Django.
    Realiza validação de login incluindo verificações de status da conta (pendente/rejeitada),
    status de ativação da conta e verificação adequada das credenciais.
    """

    def get_user(self):
        """
        Retorna o usuário autenticado se o login foi bem-sucedido.

        Returns:
            User: O objeto de usuário autenticado ou Nenhum se a autenticação falhou
        """
        return self.user_cache

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_cache = None

    def clean(self):
        """
        Valida as credenciais de login do usuário e verifica o status da conta.

        Executa as seguintes validações:
        - Verifica se o nome de usuário e a senha foram fornecidos
        - Autentica as credenciais do usuário
        - Verifica se a conta está com aprovação pendente
        - Verifica se a conta foi rejeitada
        - Verifica se a conta está ativa

        Return:
            dict: Os dados do formulário limpos se a validação for aprovada

        Raises:
            ValidationError: Se alguma verificação de validação falhar
            ObjectDoesNotExist: Se as credenciais do usuário forem inválidas
        """
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            try:
                user = User.objects.get(username=username)
                if not user.check_password(password):
                    raise ObjectDoesNotExist

                self.user_cache = user

                if hasattr(user, "perfil"):
                    if user.perfil.status == "pendente":
                        raise forms.ValidationError(
                            "Sua conta está aguardando aprovação do administrador. "
                            "Você receberá um e-mail quando sua conta for aprovada.",
                            code="pending",
                        )
                    if user.perfil.status == "rejeitado":
                        raise forms.ValidationError(
                            "Sua solicitação de cadastro foi rejeitada. "
                            "Entre em contato com o administrador para mais informações.",
                            code="rejected",
                        )

                if not user.is_active:
                    raise forms.ValidationError(
                        "Esta conta não está ativa. Por favor, verifique seu e-mail "
                        "para ativar sua conta ou entre em contato com o administrador.",
                        code="inactive",
                    )

                self.confirm_login_allowed(user)

            except ObjectDoesNotExist as err:
                raise forms.ValidationError(
                    self.error_messages["invalid_login"],
                    code="invalid_login",
                    params={"username": self.username_field.verbose_name},
                ) from err

        return self.cleaned_data


class PerfilForm(forms.ModelForm):
    """
    Formulário para gerenciar informações de perfil de usuário.
    Lida com campos como número de telefone, foto de perfil, número de registro e CPF.
    Estende o ModelForm do Django para fornecer funcionalidade de formulário para o modelo de Perfil
    """

    def clean_cpf(self):
        """Valida o formato do campo CPF"""
        cpf = self.cleaned_data.get("cpf")
        if cpf:
            # Remova quaisquer caracteres que não sejam dígitos
            cpf = "".join(filter(str.isdigit, cpf))
            if len(cpf) != 11:
                raise forms.ValidationError("CPF must contain 11 digits")
        return cpf

    def clean_telefone(self):
        """Valida o formato do campo de número de telefone"""
        telefone = self.cleaned_data.get("telefone")
        if telefone:
            # Remova quaisquer caracteres que não sejam dígitos
            telefone = "".join(filter(str.isdigit, telefone))
            if len(telefone) < 10 or len(telefone) > 11:
                raise forms.ValidationError("Phone number must contain 10 or 11 digits")
        return telefone

    class Meta:
        """
        Metaclasse para PerfilForm.
        Especifica Perfil como modelo e define quais campos devem ser incluídos no formulário,
        junto com seus rótulos e widgets.
        """

        def get_fields(self):
            """Retorna os campos definidos na classe Meta"""
            return self.fields

        def get_model(self):
            """Retorna o modelo definido na classe Meta"""
            return self.model

        model = Perfil
        fields = ["telefone", "foto", "matricula", "cpf"]
        labels = {
            "telefone": "Telefone",
            "foto": "Foto de Perfil",
            "matricula": "Matrícula",
            "cpf": "CPF",
        }
        widgets = {
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "matricula": forms.TextInput(attrs={"class": "form-control"}),
            "cpf": forms.TextInput(attrs={"class": "form-control"}),
        }
