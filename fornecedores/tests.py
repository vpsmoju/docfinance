from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Fornecedor


class FornecedorModelTest(TestCase):
    def setUp(self):
        """Configuração inicial para os testes"""
        self.fornecedor_pj = Fornecedor.objects.create(
            tipo="PJ",
            nome="Empresa Teste LTDA",
            cnpj_cpf="12345678901234",
            email="empresa@teste.com",
            telefone="(11) 1234-5678",
            endereco="Rua Teste, 123",
        )

        self.fornecedor_pf = Fornecedor.objects.create(
            tipo="PF",
            nome="João da Silva",
            cnpj_cpf="12345678901",
            email="joao@teste.com",
            telefone="(11) 98765-4321",
            endereco="Av. Teste, 456",
        )

    def test_fornecedor_creation(self):
        """Testa a criação básica de fornecedores"""
        self.assertTrue(isinstance(self.fornecedor_pj, Fornecedor))
        self.assertTrue(isinstance(self.fornecedor_pf, Fornecedor))
        self.assertEqual(self.fornecedor_pj.__str__(), "Empresa Teste LTDA")
        self.assertEqual(self.fornecedor_pf.__str__(), "João da Silva")

    def test_verbose_name_plural(self):
        """Testa o nome plural do modelo"""
        self.assertEqual(str(Fornecedor._meta.verbose_name_plural), "Fornecedores")

    def test_fornecedor_fields(self):
        """Testa os campos do modelo"""
        self.assertEqual(self.fornecedor_pj.tipo, "PJ")
        self.assertEqual(self.fornecedor_pj.nome, "Empresa Teste LTDA")
        self.assertEqual(self.fornecedor_pj.cnpj_cpf, "12345678901234")
        self.assertEqual(self.fornecedor_pj.email, "empresa@teste.com")
        self.assertEqual(self.fornecedor_pj.telefone, "(11) 1234-5678")
        self.assertEqual(self.fornecedor_pj.endereco, "Rua Teste, 123")

    def test_get_absolute_url(self):
        """Testa a URL absoluta do fornecedor"""
        url = reverse(
            "fornecedores:fornecedor_detail", kwargs={"pk": self.fornecedor_pj.pk}
        )
        self.assertEqual(self.fornecedor_pj.get_absolute_url(), url)

    def test_invalid_cnpj(self):
        """Testa validação de CNPJ inválido"""
        fornecedor = Fornecedor(
            tipo="PJ", nome="Empresa Inválida", cnpj_cpf="11111111111111"
        )
        with self.assertRaises(ValidationError):
            fornecedor.full_clean()

    def test_invalid_cpf(self):
        """Testa validação de CPF inválido"""
        fornecedor = Fornecedor(
            tipo="PF", nome="Pessoa Inválida", cnpj_cpf="11111111111"
        )
        with self.assertRaises(ValidationError):
            fornecedor.full_clean()

    def test_tipo_choices(self):
        """Testa as opções do campo tipo"""
        self.assertEqual(len(Fornecedor.TIPO_CHOICES), 2)
        self.assertIn(("PF", "Pessoa Física"), Fornecedor.TIPO_CHOICES)
        self.assertIn(("PJ", "Pessoa Jurídica"), Fornecedor.TIPO_CHOICES)

    def test_ordering(self):
        """Testa a ordenação dos fornecedores"""
        fornecedores = Fornecedor.objects.all()
        self.assertEqual(list(fornecedores), sorted(fornecedores, key=lambda x: x.nome))
