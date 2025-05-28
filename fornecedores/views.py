"""
Módulo de views para gerenciamento de fornecedores no sistema DocFinance.

Este módulo implementa as views baseadas em classe para todas as operações CRUD
(Create, Read, Update, Delete) relacionadas aos fornecedores. Inclui:

Classes:
    - FornecedorListView: Lista paginada de fornecedores com funcionalidade de busca
    - FornecedorDetailView: Exibição detalhada de um fornecedor específico
    - FornecedorCreateView: Criação de novos fornecedores com validação de permissões
    - FornecedorUpdateView: Atualização de fornecedores existentes
    - FornecedorDeleteView: Remoção de fornecedores com confirmação

Todas as views implementam:
    - Controle de acesso através de LoginRequiredMixin
    - Validação de permissões específicas onde necessário
    - Mensagens de feedback para o usuário
    - Redirecionamentos apropriados após as operações

Dependências:
    - Django's generic class-based views
    - Sistema de autenticação e permissões do Django
    - Sistema de mensagens do Django
    - Modelo Fornecedor
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import FornecedorForm
from .models import Fornecedor


class FornecedorListView(LoginRequiredMixin, ListView):
    """Lista de fornecedores com paginação."""

    model = Fornecedor
    paginate_by = 10
    ordering = ["nome"]

    def get_queryset(self):
        """Retorna o queryset de fornecedores filtrado por parâmetros de busca."""
        queryset = super().get_queryset()
        busca = self.request.GET.get("search")

        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) | Q(cnpj_cpf__icontains=busca)
            )
        return queryset

    def get_context_data(self, **kwargs):
        """Obtém dados adicionais de contexto para o template."""
        context = super().get_context_data(**kwargs)
        context["total_fornecedores"] = self.get_queryset().count()
        return context


class FornecedorDetailView(LoginRequiredMixin, DetailView):
    """Exibe os detalhes de um fornecedor específico."""

    model = Fornecedor

    def get_queryset(self):
        """Retorna o queryset de fornecedores filtrado por permissões do usuário."""
        return Fornecedor.objects.all()

    def get_context_data(self, **kwargs):
        """Obtém dados adicionais de contexto para o template."""
        context = super().get_context_data(**kwargs)
        context["titulo_pagina"] = f"Detalhes do Fornecedor - {self.object.nome}"
        return context


class FornecedorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Cria um novo fornecedor com validação de permissões."""

    def get_form(self, form_class=None):
        """Retorna a instância do formulário a ser usada na visualização."""
        form = super().get_form(form_class)
        return form

    def form_valid(self, form):
        """Valide o formulário e defina a mensagem de sucesso"""
        messages.success(self.request, "Fornecedor criado com sucesso!")
        return super().form_valid(form)

    model = Fornecedor
    form_class = FornecedorForm
    permission_required = "fornecedores.add_fornecedor"
    success_url = reverse_lazy("fornecedores:fornecedor_list")


class FornecedorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Atualiza um fornecedor existente com validação de permissões."""

    def get_queryset(self):
        """Retorna o conjunto de consultas de fornecedores filtrados pelas permissões do usuário."""
        return Fornecedor.objects.all()

    def form_valid(self, form):
        """Valide o formulário e defina a mensagem de sucesso"""
        messages.success(self.request, "Fornecedor atualizado com sucesso!")
        return super().form_valid(form)

    model = Fornecedor
    form_class = FornecedorForm
    permission_required = "fornecedores.change_fornecedor"
    success_url = reverse_lazy("fornecedores:fornecedor_list")


class FornecedorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Remove um fornecedor existente com validação de permissões."""

    def get_queryset(self):
        """Retorna o conjunto de consultas de fornecedores filtrados pelas permissões do usuário."""
        return Fornecedor.objects.all()

    model = Fornecedor
    permission_required = "fornecedores.delete_fornecedor"
    template_name = "fornecedores/fornecedor_confirm_delete.html"
    success_url = reverse_lazy("fornecedores:fornecedor_list")

    def delete(self, request, *args, **kwargs):
        """Executa a exclusão do fornecedor e exibe mensagem de sucesso."""
        messages.success(self.request, "Fornecedor excluído com sucesso!")
        return super().delete(request, *args, **kwargs)
