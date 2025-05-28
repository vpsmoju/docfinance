from django import forms

from utils.document_validators import (
    format_cnpj,
    format_cpf,
    validate_cnpj,
    validate_cpf,
)

from .models import Fornecedor


class FornecedorForm(forms.ModelForm):
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
                    cleaned_data["cnpj_cpf"] = format_cpf(cnpj_cpf)
            else:  # PJ
                valid, message = validate_cnpj(cnpj_cpf)
                if not valid:
                    self.add_error("cnpj_cpf", message)
                else:
                    cleaned_data["cnpj_cpf"] = format_cnpj(cnpj_cpf)

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
