from django import forms
from django.core.validators import MaxLengthValidator
import re

from utils.document_validators import (
    format_cnpj,
    format_cpf,
    validate_cnpj,
    validate_cpf,
)

from .models import Fornecedor


class FornecedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        """Permite máscara no campo CNPJ/CPF ao aceitar até 18 caracteres.

        Ajusta o validador de tamanho do campo do formulário para 18,
        evitando erro de "máximo 14" antes da limpeza que remove a máscara.
        """
        super().__init__(*args, **kwargs)
        cnpj_field = self.fields.get("cnpj_cpf")
        if cnpj_field:
            # Aceitar até 18 caracteres (CNPJ mascarado: 00.000.000/0000-00)
            cnpj_field.max_length = 18
            # Atualizar MaxLengthValidator existente, se houver
            for v in cnpj_field.validators:
                if isinstance(v, MaxLengthValidator):
                    v.limit_value = 18

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        cnpj_cpf = cleaned_data.get("cnpj_cpf")

        if tipo and cnpj_cpf:
            # Remove caracteres não numéricos
            cnpj_cpf = "".join(filter(str.isdigit, cnpj_cpf))

            # Validação específica por tipo
            if tipo == "PF":
                valid, message = validate_cpf(cnpj_cpf)
                if not valid:
                    self.add_error("cnpj_cpf", message)
                else:
                    # Persistir apenas dígitos para compatibilidade com validação e API
                    cleaned_data["cnpj_cpf"] = cnpj_cpf
            else:  # PJ
                valid, message = validate_cnpj(cnpj_cpf)
                if not valid:
                    self.add_error("cnpj_cpf", message)
                else:
                    # Persistir apenas dígitos para compatibilidade com validação e API
                    cleaned_data["cnpj_cpf"] = cnpj_cpf

        return cleaned_data

    class Meta:
        model = Fornecedor
        fields = [
            "tipo",
            "cnpj_cpf",
            "nome",
            "email",
            "telefone",
            "endereco",
            "banco",
            "tipo_conta",
            "agencia",
            "conta",
        ]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "cnpj_cpf": forms.TextInput(
                attrs={"class": "form-control", "id": "id_cnpj_cpf"}
            ),
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(
                attrs={"class": "form-control", "id": "id_telefone"}
            ),
            "endereco": forms.TextInput(attrs={"class": "form-control"}),
            "banco": forms.TextInput(attrs={"class": "form-control"}),
            "tipo_conta": forms.Select(attrs={"class": "form-select"}),
            "agencia": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_agencia",
                    "placeholder": "0000-0",
                }
            ),
            "conta": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_conta",
                    "placeholder": "0000000000-0",
                }
            ),
        }

    def clean_cnpj_cpf(self):
        """Remove máscara e valida tamanho conforme tipo (PF:11, PJ:14)."""
        value = self.cleaned_data.get("cnpj_cpf", "")
        digits = re.sub(r"\D", "", value)
        tipo = self.cleaned_data.get("tipo")
        if tipo == "PF":
            if len(digits) != 11:
                raise forms.ValidationError("CPF deve conter exatamente 11 dígitos.")
        else:
            if len(digits) != 14:
                raise forms.ValidationError("CNPJ deve conter exatamente 14 dígitos.")
        return digits

    def clean_telefone(self):
        """Remove máscara do telefone e valida 10 ou 11 dígitos.

        Persiste apenas dígitos. Erra se fora do padrão brasileiro (10/11).
        """
        value = self.cleaned_data.get("telefone")
        if not value:
            return value
        digits = re.sub(r"\D", "", str(value))
        if digits and len(digits) not in (10, 11):
            raise forms.ValidationError("Telefone deve conter 10 ou 11 dígitos.")
        return digits
