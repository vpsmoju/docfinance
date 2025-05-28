from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from fornecedores.models import Fornecedor

from .forms import DarBaixaForm, DocumentoForm
from .models import Documento


class DocumentoModelTest(TestCase):
    def setUp(self):
        self.fornecedor = Fornecedor.objects.create(
            nome="Fornecedor Teste", cnpj_cpf="12345678901", tipo="PF"
        )

    def test_criar_documento(self):
        doc = Documento.objects.create(
            fornecedor=self.fornecedor,
            numero=Documento.gerar_numero(),
            numero_documento="NF123",
            tipo="NF",
            data_documento=date(2024, 1, 1),
            valor_documento=Decimal("100.00"),
            valor_liquido=Decimal("100.00"),
        )
        self.assertEqual(doc.numero_documento, "NF123")

    def test_validacao_datas(self):
        doc = Documento(
            fornecedor=self.fornecedor,
            numero=Documento.gerar_numero(),
            numero_documento="NF124",
            tipo="NF",
            data_documento=date(2024, 2, 1),
            data_pagamento=date(2024, 1, 1),
            valor_documento=Decimal("100.00"),
            valor_liquido=Decimal("100.00"),
        )
        with self.assertRaises(ValidationError):
            doc.clean()

    def test_valor_positivo(self):
        doc = Documento(
            fornecedor=self.fornecedor,
            numero=Documento.gerar_numero(),
            numero_documento="NF125",
            tipo="NF",
            data_documento=date(2024, 1, 1),
            valor_documento=Decimal("-100.00"),
            valor_liquido=Decimal("100.00"),
        )
        with self.assertRaises(ValidationError):
            doc.clean()


class DocumentoFormTest(TestCase):
    def setUp(self):
        self.fornecedor = Fornecedor.objects.create(
            nome="Fornecedor Teste", cnpj_cpf="12345678901", tipo="PF"
        )
        self.form_data = {
            "fornecedor": self.fornecedor.id,
            "numero_documento": "NF126",
            "tipo": "NF",
            "data_documento": "2024-01-01",
            "valor_documento": "100.00",
            "valor_liquido": "100.00",
            "valor_irrf": "0.00",
            "valor_iss": "0.00",
            "status": "PEN",
            "secretaria": "ADM",  # Campo adicionado
            "recurso": "GABINETE",  # Campo adicionado
            "descricao": "Teste de documento",  # Campo adicionado
        }

    def test_documento_form_valido(self):
        form = DocumentoForm(data=self.form_data)
        if not form.is_valid():
            print(form.errors)  # Para debug
        self.assertTrue(form.is_valid())


class DarBaixaFormTest(TestCase):
    def setUp(self):
        self.fornecedor = Fornecedor.objects.create(
            nome="Fornecedor Teste", cnpj_cpf="12345678901", tipo="PF"
        )
        self.documento = Documento.objects.create(
            fornecedor=self.fornecedor,
            numero=Documento.gerar_numero(),
            numero_documento="NF127",
            tipo="NF",
            data_documento=date(2024, 1, 1),
            valor_documento=Decimal("100.00"),
            valor_liquido=Decimal("100.00"),
        )

    def test_dar_baixa_form_valido(self):
        form_data = {"data_pagamento": "2024-02-01"}
        form = DarBaixaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_dar_baixa_form_data_invalida(self):
        form_data = {
            "data_pagamento": "2024-13-01"  # Mês inválido
        }
        form = DarBaixaForm(data=form_data)
        self.assertFalse(form.is_valid())
