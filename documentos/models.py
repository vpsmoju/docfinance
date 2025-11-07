"""Modelos para documentos financeiros.

Este módulo contém modelos para gerenciamento de documentos financeiros e fornecedores,
incluindo funcionalidades de rastreamento, validação e processamento de documentos.

Models:
    Fornecedor: Represents document suppliers/vendors
    Documento: Represents financial documents with tracking and validation
"""

import datetime
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from fornecedores.models import Fornecedor


class Secretaria(models.Model):
    """Modelo de Secretaria (dinâmico)."""

    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    codigo = models.CharField(
        max_length=20, unique=True, verbose_name="Código/Sigla"
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Secretaria"
        verbose_name_plural = "Secretarias"

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Recurso(models.Model):
    """Modelo de Recurso vinculado a uma Secretaria (dinâmico)."""

    nome = models.CharField(max_length=100, verbose_name="Nome")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    secretaria = models.ForeignKey(
        Secretaria, on_delete=models.CASCADE, related_name="recursos"
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Documento(models.Model):
    """
    Modelo para representar documentos financeiros.
    Armazena informações como número, tipo, fornecedor, valores e status.
    """

    TIPO_CHOICES = [
        ("NF", "Nota Fiscal"),
        ("NFS", "Nota Fiscal de Serviço"),
        ("NFSA", "Nota Fiscal de Serviço Avulsa"),
        ("FAT", "Fatura"),
        ("REC", "Recibo"),
    ]

    STATUS_CHOICES = [
        ("PEN", "Pendente"),
        ("PAG", "Pago"),
        ("ATR", "Atrasado"),
    ]

    ETAPA_CHOICES = [
        ("ABERTURA", "Abertura de Processo"),
        ("CONTROLE_INTERNO", "Controle Interno"),
        ("EMPENHO", "Empenho"),
        ("PAGAMENTO", "Pagamento"),
        ("BAIXA", "Baixa"),
    ]


    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.CASCADE, verbose_name="Fornecedor"
    )
    numero = models.CharField(max_length=20, unique=True, verbose_name="Número")
    numero_documento = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Número do Documento"
    )
    tipo = models.CharField(max_length=4, choices=TIPO_CHOICES, verbose_name="Tipo")
    data_documento = models.DateField(verbose_name="Data do Documento")
    data_pagamento = models.DateField(
        verbose_name="Data de Pagamento", blank=True, null=True
    )  # Tornando opcional
    data_entrada = models.DateTimeField(auto_now_add=True)
    etapa = models.CharField(
        max_length=20,
        choices=ETAPA_CHOICES,
        default="ABERTURA",
        verbose_name="Etapa do Processo",
    )
    valor_documento = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Bruto"
    )
    valor_irrf = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Valor IRRF"
    )
    valor_iss = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Valor ISS"
    )
    valor_liquido = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Líquido"
    )
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    status = models.CharField(
        max_length=3, choices=STATUS_CHOICES, default="PEN", verbose_name="Status"
    )
    data_baixa = models.DateTimeField(
        blank=True, null=True, verbose_name="Data de Baixa"
    )
    baixado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_baixados",
    )

    # Novos campos (dinâmicos via FK)
    secretaria = models.ForeignKey(
        Secretaria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Secretaria",
        related_name="documentos",
    )

    recurso = models.ForeignKey(
        Recurso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Recurso",
        related_name="documentos",
    )

    class Meta:
        """Metadados do modelo Documento."""

        permissions = [
            ("dar_baixa_documento", "Pode dar baixa em documentos"),
        ]
        ordering = ["-data_documento"]
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

    def __str__(self):
        """Retorna uma representação em string do documento."""
        return f"{self.numero} - {self.fornecedor.nome}"  # pylint: disable=no-member

    def save(self, *args, **kwargs):
        """Sobrescreve o método save para garantir que a validação clean() seja chamada
        antes de salvar o objeto no banco de dados.

        Args:
            *args: Argumentos posicionais para o método save original.
            **kwargs: Argumentos nomeados para o método save original.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Validações e ajustes automáticos antes de salvar.

        - Garante que para tipos "Nota Fiscal" (NF) e "Fatura" (FAT) não haja descontos
          de ISS/IRRF (sempre zero).
        - Recalcula `valor_liquido` como `valor_documento - valor_iss - valor_irrf`.
        - Impede valores negativos em campos monetários.
        - Valida coerência básica de datas em relação ao status de pagamento.
        """
        super().clean()

        # Normalização de campos numéricos para evitar None
        self.valor_documento = self.valor_documento or Decimal("0")
        self.valor_iss = self.valor_iss or Decimal("0")
        self.valor_irrf = self.valor_irrf or Decimal("0")

        # Regra: NF/FAT não possuem descontos (ISS/IRRF sempre zero)
        if self.tipo in ("NF", "FAT"):
            self.valor_iss = Decimal("0")
            self.valor_irrf = Decimal("0")

        # Impedir valores negativos em descontos
        if self.valor_iss < 0:
            raise ValidationError({"valor_iss": "O valor de ISS não pode ser negativo."})
        if self.valor_irrf < 0:
            raise ValidationError({"valor_irrf": "O valor de IRRF não pode ser negativo."})
        if self.valor_documento < 0:
            raise ValidationError({"valor_documento": "O valor do documento não pode ser negativo."})

        # Recalcular valor líquido sempre com base nas regras acima
        self.valor_liquido = self.valor_documento - self.valor_iss - self.valor_irrf

        if self.valor_liquido < 0:
            raise ValidationError({"valor_liquido": "O valor líquido não pode ser negativo."})

        # Coerência de datas com status
        if self.status == "PAG" and not self.data_pagamento:
            raise ValidationError({"data_pagamento": "A data de pagamento é obrigatória quando o status é Pago."})
        if self.status != "PAG" and self.data_pagamento is not None:
            # Se não está pago, remover data de pagamento para manter consistência
            self.data_pagamento = None

    @staticmethod
    def gerar_numero():
        """
        Gera um número único no formato DDMMAAAAHHMMSS0000.

        Retorna:
            str: Número único gerado para o documento.
        """
        agora = timezone.now()
        prefixo = agora.strftime("%d%m%Y%H%M%S")

        # Buscar o último documento do dia
        hoje = datetime.date.today()
        documentos_hoje = Documento.objects.filter(  # pylint: disable=no-member
            data_entrada__year=hoje.year,
            data_entrada__month=hoje.month,
            data_entrada__day=hoje.day,
        ).order_by("-numero")

        if documentos_hoje.exists():
            ultimo_doc = documentos_hoje.first()
            try:
                # Extrair o sequencial (últimos 4 dígitos)
                sequencial = int(ultimo_doc.numero[-4:])
                sequencial += 1
            except (ValueError, IndexError):
                sequencial = 1
        else:
            sequencial = 1

        # Formatar o sequencial com zeros à esquerda
        sequencial_str = f"{sequencial:04d}"

        return f"{prefixo}{sequencial_str}"

    def gerar_numero_documento(self):
        """
        Gera um número único no formato DDMMAAAAHHMMSS0000.

        Retorna:
            str: Número único gerado para o documento.
        """
        agora = timezone.now()
        prefixo = agora.strftime("%d%m%Y%H%M%S")

        # Buscar o último documento do dia
        hoje = datetime.date.today()
        documentos_hoje = Documento.objects.filter(  # pylint: disable=no-member
            data_entrada__year=hoje.year,
            data_entrada__month=hoje.month,
            data_entrada__day=hoje.day,
        ).order_by("-numero")

        if documentos_hoje.exists():
            ultimo_doc = documentos_hoje.first()
            try:
                # Extrair o sequencial (últimos 4 dígitos)
                sequencial = int(ultimo_doc.numero[-4:])
                sequencial += 1
            except (ValueError, IndexError):
                sequencial = 1
        else:
            sequencial = 1

        # Formatar o sequencial com zeros à esquerda
        sequencial_str = f"{sequencial:04d}"

        return f"{prefixo}{sequencial_str}"


class HistoricoDocumento(models.Model):
    """Registra histórico de alterações de etapa em um documento."""

    documento = models.ForeignKey(
        "Documento", on_delete=models.CASCADE, related_name="historicos"
    )
    etapa = models.CharField(max_length=20, choices=Documento.ETAPA_CHOICES)
    descricao = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_hora"]
        verbose_name = "Histórico de Documento"
        verbose_name_plural = "Históricos de Documento"

    def __str__(self):
        return f"{self.documento.numero} - {self.get_etapa_display()} em {self.data_hora}"

    def clean(self):
        """Realiza validações personalizadas antes de salvar o objeto."""
        super().clean()

        # Validar valores negativos
        if self.valor_documento and self.valor_documento < 0:
            raise ValidationError(
                {"valor_documento": "O valor do documento não pode ser negativo."}
            )

        if self.valor_liquido and self.valor_liquido < 0:
            raise ValidationError(
                {"valor_liquido": "O valor líquido não pode ser negativo."}
            )

        # Validar datas
        if (
            self.data_documento
            and self.data_pagamento
            and self.data_documento > self.data_pagamento
        ):
            raise ValidationError(
                {
                    "data_pagamento": "A data de pagamento não pode ser anterior à data do documento."
                }
            )

        # Verificar se o status é 'Pago' e se a data de pagamento está vazia
        if self.status == "PAG" and not self.data_pagamento:
            raise ValidationError(
                {
                    "data_pagamento": "A data de pagamento é obrigatória quando o status é Pago."
                }
            )

        # Verificar se o status não é 'Pago' mas a data de pagamento está preenchida
        if self.status != "PAG" and self.data_pagamento:
            self.data_pagamento = None
