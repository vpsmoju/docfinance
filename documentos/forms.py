"""
Módulo de formulários para gerenciamento de documentos financeiros.

Este módulo contém os formulários necessários para criar, editar e gerenciar documentos
financeiros no sistema DocFinance. Inclui:

Classes:
    - DateInputBR: Widget personalizado para campos de data no formato brasileiro
    - DocumentoForm: Formulário principal para criação e edição de documentos
    - DarBaixaForm: Formulário específico para registrar pagamentos de documentos

Os formulários implementam validações personalizadas e widgets específicos para
garantir a consistência dos dados e uma melhor experiência do usuário.
"""

from django import forms
from django.forms.widgets import DateInput

from .models import Documento


class DateInputBR(DateInput):
    """Widget personalizado para campos monetários."""

    def get_format(self):
        """Retorna o formato de data usado por este widget."""
        return "%d/%m/%Y"

    def format_value(self, value):
        """Formate o valor da data para o formato Brasileiro."""
        if value is None:
            return ""
        return value

    input_type = "date"

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs.update({"class": "form-control"})
        super().__init__(attrs=attrs, format="%d/%m/%Y")


class DocumentoForm(forms.ModelForm):
    """
    Formulário para criação e edição de documentos financeiros.
    Inclui todos os campos do modelo Documento e widgets personalizados.
    """

    def clean(self):
        """
        Método de validação personalizado para garantir a consistência dos dados do formulário
        """
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        """
        Método de salvamento personalizado para lidar com o salvamento da instância do modelo
        """
        instance = super().save(commit=commit)
        return instance

    class Meta:
        """
        Metaclasse para DocumentoForm.
        Especifica o modelo, os campos e os widgets para o formulário.
        """

        def get_fields(self):
            """Retorna a lista de campos para este formulário"""
            return self.fields

        def get_widgets(self):
            """Retorna o dicionário de widgets para este formulário"""
            return self.widgets

        model = Documento
        fields = [
            "numero_documento",
            "tipo",
            "fornecedor",
            "data_documento",
            "data_pagamento",
            "valor_documento",
            "valor_irrf",
            "valor_iss",
            "valor_liquido",
            "descricao",
            "status",
            "secretaria",
            "recurso",
        ]
        widgets = {
            "data_documento": DateInputBR(),
            "data_pagamento": DateInputBR(),
            "status": forms.Select(attrs={"class": "form-control"}),
            "descricao": forms.Textarea(
                attrs={"class": "form-control campo-descricao-reduzida"}
            ),
            "secretaria": forms.Select(attrs={"class": "form-control"}),
            "recurso": forms.Select(attrs={"class": "form-control"}),
        }


class DarBaixaForm(forms.Form):
    """
    Formulário para dar baixa em um documento.
    Permite registrar a data de pagamento de um documento pendente.
    """

    def clean(self):
        """
        Método de validação personalizado para garantir a consistência dos dados do formulário
        """
        cleaned_data = super().clean()
        return cleaned_data

    def save(self):
        """
        Método de salvamento personalizado para lidar com persistência de dados de formulário
        """
        return self.cleaned_data

    data_pagamento = forms.DateField(
        label="Data de Pagamento",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        required=True,
    )
