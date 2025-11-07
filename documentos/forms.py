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
import re
from django.forms.widgets import DateInput

from .models import Documento, Recurso, Secretaria


class DateInputBR(DateInput):
    """Widget de data usando input nativo do navegador.

    O valor do input type="date" deve estar em formato ISO (YYYY-MM-DD).
    Esta classe garante que valores existentes em edição sejam renderizados
    corretamente, independentemente do locale desejado.
    """

    input_type = "date"

    def get_format(self):
        """Usa o formato ISO para garantir renderização em inputs de data."""
        return "%Y-%m-%d"

    def format_value(self, value):
        """Converte o valor para ISO (YYYY-MM-DD) quando possível."""
        if value is None:
            return ""
        # Valor como string já ISO
        if isinstance(value, str):
            # Normaliza casos 'DD/MM/AAAA' para ISO, se aplicável
            import re
            m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", value)
            if m:
                d, mth, y = m.groups()
                return f"{y}-{mth}-{d}"
            return value
        # Valor como date/datetime
        try:
            return value.strftime("%Y-%m-%d")
        except Exception:
            return super().format_value(value)

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs.update({"class": "form-control"})
        super().__init__(attrs=attrs, format="%Y-%m-%d")


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Popular dinamicamente com os modelos
        self.fields["secretaria"].queryset = Secretaria.objects.all()
        self.fields["recurso"].queryset = Recurso.objects.all()


class SecretariaForm(forms.ModelForm):
    class Meta:
        model = Secretaria
        # Removemos o campo 'codigo' do formulário de criação/edição padrão
        fields = ["nome"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Gerar código automático de até 4 letras (sigla)
        if not instance.codigo:
            nome = (instance.nome or "COD").strip()
            # Construir sigla pelas iniciais das palavras (até 4 letras)
            tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", nome)
            iniciais = "".join(t[0] for t in tokens).upper()
            # Remover acentos e caracteres não A-Z
            iniciais = re.sub(r"[^A-Z]", "", iniciais)
            sigla = (iniciais[:4] or re.sub(r"[^A-Z]", "", nome.upper())[:4] or "COD")

            codigo = sigla
            original = codigo
            i = 1
            while Secretaria.objects.filter(codigo=codigo).exists():
                i += 1
                codigo = f"{original}{i}"
            instance.codigo = codigo
        if commit:
            instance.save()
        return instance


class RecursoForm(forms.ModelForm):
    class Meta:
        model = Recurso
        # Removemos o campo 'codigo' (será gerado automaticamente)
        fields = ["nome", "secretaria"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "secretaria": forms.Select(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Gerar código automaticamente se não existir
        if not instance.codigo:
            base = instance.nome or "COD"
            slug = re.sub(r"[^A-Z0-9]+", "", base.upper()) or "COD"
            prefix = instance.secretaria.codigo if instance.secretaria and instance.secretaria.codigo else "REC"
            codigo = f"{prefix}_{slug}"
            original = codigo
            i = 1
            while Recurso.objects.filter(codigo=codigo).exists():
                i += 1
                codigo = f"{original}{i}"
            instance.codigo = codigo
        if commit:
            instance.save()
        return instance


class CadastroSecretariaRecursoForm(forms.Form):
    """
    Formulário unificado para cadastrar Secretaria e Recurso de uma vez.
    Remove os campos de código e gera automaticamente com base no nome.
    """

    secretaria_nome = forms.CharField(
        label="Nome da Secretaria",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    recurso_nome = forms.CharField(
        label="Nome do Recurso",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def save(self):
        sec_nome = self.cleaned_data["secretaria_nome"].strip()
        rec_nome = self.cleaned_data["recurso_nome"].strip()

        # Secretaria: cria ou obtém por nome; gera código se necessário
        secretaria, created_sec = Secretaria.objects.get_or_create(
            nome=sec_nome
        )
        if created_sec or not secretaria.codigo:
            # Gerar sigla de até 4 letras pelas iniciais
            tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", sec_nome)
            iniciais = "".join(t[0] for t in tokens).upper()
            iniciais = re.sub(r"[^A-Z]", "", iniciais)
            sigla = (iniciais[:4] or re.sub(r"[^A-Z]", "", sec_nome.upper())[:4] or "COD")
            codigo = sigla
            original = codigo
            i = 1
            while Secretaria.objects.filter(codigo=codigo).exists():
                i += 1
                codigo = f"{original}{i}"
            secretaria.codigo = codigo
            secretaria.save()

        # Recurso: cria ou obtém por nome vinculado à secretaria; gera código
        recurso, created_rec = Recurso.objects.get_or_create(
            nome=rec_nome,
            secretaria=secretaria,
        )
        if created_rec or not recurso.codigo:
            base = rec_nome or "COD"
            slug = re.sub(r"[^A-Z0-9]+", "", base.upper()) or "COD"
            prefix = secretaria.codigo or "REC"
            codigo = f"{prefix}_{slug}"
            original = codigo
            i = 1
            while Recurso.objects.filter(codigo=codigo).exists():
                i += 1
                codigo = f"{original}{i}"
            recurso.codigo = codigo
            recurso.save()

        return secretaria, recurso


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


class AtualizarEtapaForm(forms.Form):
    """Formulário para atualizar a etapa do processo do documento."""

    etapa = forms.ChoiceField(choices=Documento.ETAPA_CHOICES, label="Nova etapa")
    MOTIVOS_DEVOLUCAO = [
        ("PEND_DOC", "Pendência documental"),
        ("ERRO_EMP", "Erro no empenho"),
        ("AJUSTE_VAL", "Ajuste de valores"),
        ("DIV_DADOS", "Divergência de dados"),
        ("SOL_SEC", "Solicitação da secretaria"),
        ("OUTRO", "Outro"),
    ]
    motivo_tipo = forms.ChoiceField(
        choices=MOTIVOS_DEVOLUCAO,
        required=False,
        label="Motivo da devolução (opções)",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    motivo_livre = forms.CharField(
        label="Detalhe/observação (opcional)",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
    descricao = forms.CharField(
        label="Descrição (opcional)",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
