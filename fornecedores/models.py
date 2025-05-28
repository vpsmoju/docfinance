# Organizar imports em ordem alfabética e separar imports de terceiros
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from utils.document_validators import validate_cnpj, validate_cpf


def validate_cnpj_cpf(value):
    """Validador para CNPJ/CPF"""
    value = "".join(filter(str.isdigit, value))
    if not value.isdigit():
        raise ValidationError("CNPJ/CPF deve conter apenas números")
    return value


class Fornecedor(models.Model):
    """
    Modelo para representar fornecedores de documentos financeiros.
    Armazena informações básicas como nome, tipo (PF/PJ), CNPJ/CPF e contato.
    """

    TIPO_CHOICES = [
        ("PF", "Pessoa Física"),
        ("PJ", "Pessoa Jurídica"),
    ]

    TIPO_CONTA_CHOICES = [
        ("CC", "Conta Corrente"),
        ("PP", "Poupança"),
    ]

    # Campos básicos
    tipo = models.CharField(
        max_length=2, choices=TIPO_CHOICES, default="PJ", verbose_name="Tipo"
    )
    nome = models.CharField(max_length=200, verbose_name="Nome")
    cnpj_cpf = models.CharField(
        max_length=14,
        unique=True,
        verbose_name="CNPJ/CPF",
        validators=[validate_cnpj_cpf],
    )
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    telefone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Telefone"
    )
    endereco = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Endereço"
    )

    # Campos de dados bancários
    banco = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Banco"
    )
    tipo_conta = models.CharField(
        max_length=2,
        choices=TIPO_CONTA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Tipo de Conta",
    )
    agencia = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        verbose_name="Agência",
        help_text="Formato: 0000 ou 0000-0",
    )
    conta = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name="Conta",
        help_text="Formato: 0000000000-0",
    )

    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ["nome"]

    def __str__(self):
        return str(self.nome)

    def get_absolute_url(self):
        return reverse("fornecedores:fornecedor_detail", kwargs={"pk": self.pk})

    def clean(self):
        """Validação do modelo para garantir o formato correto do CNPJ/CPF e dados bancários"""
        super().clean()

        # Validar CNPJ/CPF
        if self.tipo and self.cnpj_cpf:
            cnpj_cpf = "".join(filter(str.isdigit, self.cnpj_cpf))

            if self.tipo == "PF":
                valid, message = validate_cpf(cnpj_cpf)
                if not valid:
                    raise ValidationError({"cnpj_cpf": message})
            else:  # PJ
                valid, message = validate_cnpj(cnpj_cpf)
                if not valid:
                    raise ValidationError({"cnpj_cpf": message})

        # Validar formato da agência
        if self.agencia:
            agencia_sem_hifen = str(self.agencia).replace("-", "")
            formato_valido = (
                (
                    len(str(self.agencia)) == 4 and str(self.agencia).isdigit()
                )  # Formato: 0000
                or (
                    len(str(self.agencia)) == 6
                    and str(self.agencia)[4] == "-"
                    and agencia_sem_hifen.isdigit()
                )  # Formato: 0000-0
            )
            if not formato_valido:
                raise ValidationError(
                    {"agencia": "Formato inválido. Use 0000 ou 0000-0"}
                )

        # Validar formato da conta
        if self.conta and not (
            len(self.conta) == 12
            and str(self.conta)[10] == "-"
            and str(self.conta).replace("-", "").isdigit()
        ):
            raise ValidationError({"conta": "Formato inválido. Use 0000000000-0"})
