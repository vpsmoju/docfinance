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
        help_text="Formato: 0000 ou 0000-0 (dígito pode ser X)",
    )
    conta = models.CharField(
        max_length=12,
        blank=True,
        null=True,
        verbose_name="Conta",
        help_text="Formato: 0000000000-0 (dígito pode ser X)",
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

        # Validar formato da agência (suporta dígito verificador 'X')
        if self.agencia:
            agencia = str(self.agencia)
            if (
                len(agencia) == 4 and agencia.isdigit()
            ):
                pass  # Formato: 0000
            elif (
                len(agencia) == 6
                and agencia[0:4].isdigit()
                and agencia[4] == "-"
                and (agencia[5].isdigit() or agencia[5].lower() == "x")
            ):
                pass  # Formato: 0000-0 ou 0000-X
            else:
                raise ValidationError(
                    {"agencia": "Formato inválido. Use 0000 ou 0000-0 (dígito pode ser X)"}
                )

        # Validar formato da conta
        if self.conta:
            conta = str(self.conta)
            # Permitir 1 a 11 dígitos antes do hífen e 1 dígito/letter 'X' após
            partes = conta.split("-")
            dv_valido = (
                len(partes) == 2
                and len(partes[1]) == 1
                and (partes[1].isdigit() or partes[1].lower() == "x")
            )
            if (
                len(partes) != 2
                or not partes[0].isdigit()
                or not dv_valido
                or len(partes[0]) < 1
                or len(partes[0]) > 11
            ):
                raise ValidationError({
                    "conta": "Formato inválido. Use padrões como 12-3, 1234-5 ou dígito X"
                })
