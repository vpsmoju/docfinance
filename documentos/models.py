"""Modelos para documentos financeiros.

Este módulo contém modelos para gerenciamento de documentos financeiros e fornecedores,
incluindo funcionalidades de rastreamento, validação e processamento de documentos.

Models:
    Fornecedor: Represents document suppliers/vendors
    Documento: Represents financial documents with tracking and validation
"""

import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from fornecedores.models import Fornecedor


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

    # Opções para o campo Secretaria
    SECRETARIA_CHOICES = [
        ("ADM", "Sec. de Administração"),
        ("ASS", "Sec. de Assistência"),
        ("EDU", "Sec. de Educação"),
        ("SAU", "Sec. de Saúde"),
    ]

    # Opções para o campo Recurso
    RECURSO_CHOICES_EDU = [
        ("FUNDEB", "FUNDEB"),
        ("DMDE", "DMDE"),
        ("QSE", "QSE"),
        ("PNAE", "PNAE"),
        ("PETE", "PETE"),
        ("PEAE", "PEAE"),
        ("PNAT", "PNAT"),
        ("SEDUC_CRECHE", "SEDUC/CRECHE"),
        ("MOJU_EDUCA", "MOJU-EDUCA"),
        ("BRALF", "BRALF"),
        ("PDDE", "PDDE"),
        ("CONVENIO_EDU", "CONVÊNIO"),
    ]

    RECURSO_CHOICES_ADM = [
        ("GABINETE", "GABINETE"),
        ("PREFEITURA", "PREFEITURA"),
        ("SEMAD", "SEMAD"),
        ("SEOB", "SEOB"),
        ("SECTEMA", "SECTEMA"),
        ("ILUM_PUBLICA", "ILUM. PÚBLICA"),
        ("SEMUSP", "SEMUSP"),
        ("SEMAGRI", "SEMAGRI"),
        ("LEI_ALDIR_BLANC", "LEI ALDIR BLANC"),
        ("SECULT", "SECULT"),
        ("SEMAPI", "SEMAPI"),
        ("SETRANS", "SETRANS"),
        ("SEMDESTRE", "SEMDESTRE"),
        ("SEFAZ", "SEFAZ"),
        ("SECDELT", "SECDELT"),
        ("CONVENIO_ADM", "CONVÊNIO"),
    ]

    RECURSO_CHOICES_ASS = [
        ("FMAS", "FMAS"),
        ("IGD_IGPAB", "IGD/IGPAB"),
        ("PSB", "PSB"),
        ("MAC", "MAC"),
        ("GSUAS", "GSUAS"),
        ("PROT_ESPECIAL", "PROT_ESPECIAL"),
        ("PROT_BASICA", "PROT_BASICA"),
        ("BL_IGD", "BL IGD"),
        ("PROCAD_SUAS", "PROCAD-SUAS"),
        ("CRIAN_FELIZ", "CRIAN_FELIZ"),
        ("AUX_BRASIL", "AUX_BRASIL"),
        ("CONVENIO_ASS", "CONVÊNIO"),
    ]

    RECURSO_CHOICES_SAU = [
        ("PISO_ENFER", "PISO ENFER"),
        ("CONTRAPARTIDA", "CONTRAPARTIDA"),
        ("FUS", "FUS"),
        ("OUTROS", "OUTROS"),
        ("CONVENIO_SAU", "CONVÊNIO"),
    ]

    # Combinando todas as opções de recurso
    RECURSO_CHOICES = (
        RECURSO_CHOICES_EDU
        + RECURSO_CHOICES_ADM
        + RECURSO_CHOICES_ASS
        + RECURSO_CHOICES_SAU
    )

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

    # Novos campos
    secretaria = models.CharField(
        max_length=3,
        choices=SECRETARIA_CHOICES,
        verbose_name="Secretaria",
        blank=True,
        null=True,
    )

    recurso = models.CharField(
        max_length=20,
        choices=RECURSO_CHOICES,
        verbose_name="Recurso",
        blank=True,
        null=True,
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
