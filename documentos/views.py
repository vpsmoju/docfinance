"""
Módulo de views para o aplicativo de documentos financeiros.
Contém as classes e funções para gerenciar documentos.
"""

# Imports da biblioteca padrão
import logging
import traceback
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import localtime

# Imports de terceiros
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from .api import buscar_fornecedor_por_cnpj_cpf

# Nas importações no topo do arquivo
from .forms import DarBaixaForm, DocumentoForm

# Imports locais
from .models import Documento

# Configurar o logger
logger = logging.getLogger(__name__)


class DocumentoListView(LoginRequiredMixin, ListView):
    """Lista de documentos com paginação."""

    def get_context_data(self, **kwargs):
        """Obtém dados adicionais de contexto para o template."""
        context = super().get_context_data(**kwargs)
        context["total_documentos"] = self.get_queryset().count()
        return context

    model = Documento
    template_name = "documentos/documento_list.html"
    context_object_name = "object_list"
    paginate_by = 10
    ordering = ["-data_documento"]

    def get_queryset(self):
        """Filtra os documentos com base na pesquisa."""
        queryset = super().get_queryset()
        search = self.request.GET.get("search")

        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search)
                | Q(fornecedor__nome__icontains=search)
                | Q(descricao__icontains=search)
            )

        return queryset


class DocumentoDetailView(LoginRequiredMixin, DetailView):
    """Exibe os detalhes de um documento financeiro específico."""

    model = Documento
    template_name = "documentos/documento_detail.html"

    def get_queryset(self):
        """Retorna o queryset de documentos filtrado por permissões do usuário."""
        queryset = Documento.objects.all()
        return queryset

    def get_context_data(self, **kwargs):
        """Obtém dados adicionais de contexto para o template."""
        context = super().get_context_data(**kwargs)
        context["titulo_pagina"] = f"Detalhes do Documento - {self.object.numero}"
        return context

    model = Documento


class DocumentoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Cria um novo documento financeiro com validação de permissões."""

    model = Documento
    permission_required = "documentos.add_documento"
    form_class = DocumentoForm  # Usar o formulário personalizado
    success_url = reverse_lazy("documentos:list")

    def get_initial(self):
        """Define valores iniciais para o formulário."""
        initial = super().get_initial()
        # Definir status padrão como pendente
        initial["status"] = "PEN"
        return initial

    def form_valid(self, form):
        """Processa o formulário de criação quando válido."""
        try:
            logger.info("Iniciando processamento do formulário de criação de documento")
            logger.info("Dados do POST: %s", self.request.POST)
            logger.info(
                "Usuário que está criando o documento: %s", self.request.user.username
            )

            # Definir o número do documento automaticamente se estiver vazio ou temporário
            if not form.instance.numero or form.instance.numero.startswith("TEMP_"):
                # Use localtime para converter para o fuso horário local
                form.instance.numero = (
                    f"{localtime(timezone.now()).strftime('%d%m%Y%H%M%S')}001"
                )
                logger.info("Número gerado: %s", form.instance.numero)

            # Verificar se o formulário é válido e definir status padrão se necessário
            if form.is_valid():
                documento = form.save(commit=False)
                if not documento.status:  # Se o status não estiver definido
                    documento.status = (
                        "PEN"  # Define como pendente ou outro valor padrão
                    )

            # Log detalhado dos dados do formulário
            logger.info("Iniciando processamento do formulário de criação de documento")
            logger.info("Dados do POST: %s", self.request.POST)

            # Verificar se os campos estão vazios e usar os valores dos campos personalizados
            if not form.instance.valor_documento and "valor_bruto" in self.request.POST:
                valor_bruto = self.request.POST.get("valor_bruto", "0")
                logger.info("Usando valor_bruto do POST: %s", valor_bruto)
                form.instance.valor_documento = Decimal(valor_bruto)

            if not form.instance.valor_iss and "valor_iss" in self.request.POST:
                valor_iss = self.request.POST.get("valor_iss", "0")
                logger.info("Usando valor_iss do POST: %s", valor_iss)
                form.instance.valor_iss = Decimal(valor_iss)

            if not form.instance.valor_irrf and "valor_irrf" in self.request.POST:
                valor_irrf = self.request.POST.get("valor_irrf", "0")
                logger.info("Usando valor_irrf do POST: %s", valor_irrf)
                form.instance.valor_irrf = Decimal(valor_irrf)

            if not form.instance.valor_liquido and "valor_liquido" in self.request.POST:
                valor_liquido = self.request.POST.get("valor_liquido", "0")
                logger.info("Usando valor_liquido do POST: %s", valor_liquido)
                form.instance.valor_liquido = Decimal(valor_liquido)

            # Registrar o usuário que está criando o documento
            form.instance.baixado_por = self.request.user
            logger.info("Usuário que está criando o documento: %s", self.request.user)

            # Log dos valores finais antes de salvar
            logger.info("Valores finais antes de salvar:")
            logger.info("valor_documento: %s", form.instance.valor_documento)
            logger.info("valor_iss: %s", form.instance.valor_iss)
            logger.info("valor_irrf: %s", form.instance.valor_irrf)
            logger.info("valor_liquido: %s", form.instance.valor_liquido)

            # Verificar se o fornecedor existe
            if form.instance.fornecedor:
                logger.info(
                    "Fornecedor selecionado: %s (ID: %s)",
                    form.instance.fornecedor.nome,
                    form.instance.fornecedor.id,
                )
            else:
                logger.warning("Nenhum fornecedor selecionado!")

            # Log de erros do formulário
            if form.errors:
                logger.error("Erros do formulário: %s", form.errors)

            # Adicionar logs em vez de prints
            logger.debug("Dados do formulário: %s", self.request.POST)
            logger.debug("Erros do formulário: %s", form.errors)

            logger.info("Chamando super().form_valid(form)")
            return super().form_valid(form)
        except ValidationError as e:
            logger.error("Erro de validação ao salvar formulário: %s", e)
            messages.error(self.request, f"Erro de validação: {e}")
            return super().form_invalid(form)
        except ValueError as e:
            logger.error("Erro de valor ao salvar formulário: %s", e)
            messages.error(self.request, f"Erro de valor: {e}")
            return super().form_invalid(form)
        except (TypeError, AttributeError) as e:
            logger.error("Erro de tipo ao salvar formulário: %s", e)
            logger.error(traceback.format_exc())
            messages.error(self.request, f"Erro de tipo: {e}")
            return super().form_invalid(form)
        except (
            Exception
        ) as e:  # Mantido para capturar erros inesperados, mas com log detalhado
            logger.error("Erro inesperado ao salvar formulário: %s", e)
            logger.error(traceback.format_exc())
            messages.error(self.request, f"Erro inesperado: {e}")
            return super().form_invalid(form)

    def form_invalid(self, form):
        """Processa o formulário quando inválido e exibe mensagens de erro."""
        # Remover prints e usar apenas logs
        logger.warning("Formulário inválido!")
        logger.error("Erros do formulário: %s", form.errors)
        # Registrar erros no log
        logger.error("Erros de validação do formulário: %s", form.errors)
        # Adicionar mensagens de erro para o usuário
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Erro no campo {field}: {error}")
        return super().form_invalid(form)


class DocumentoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Atualiza um documento financeiro existente com validação de permissões."""

    model = Documento
    permission_required = "documentos.change_documento"
    form_class = DocumentoForm
    success_url = reverse_lazy("documentos:list")

    def get_initial(self):
        """Define valores iniciais para o formulário de edição."""
        initial = super().get_initial()
        documento = self.get_object()
        # Garantir que os campos iniciais estejam preenchidos
        initial["status"] = documento.status
        return initial

    def form_valid(self, form):
        """Processa o formulário de edição quando válido e salva as alterações."""
        try:
            # Verificar se o formulário é válido e definir status padrão se necessário
            if form.is_valid():
                documento = form.save(commit=False)
                if not documento.status:  # Se o status não estiver definido
                    documento.status = (
                        "PEN"  # Define como pendente ou outro valor padrão
                    )

            # Se o status não foi fornecido, manter o original
            if not form.cleaned_data.get("status"):
                documento = self.get_object()
                form.instance.status = documento.status

            # Log detalhado dos dados do formulário
            logger.info("Iniciando processamento do formulário de edição de documento")
            logger.info("Dados do POST: %s", self.request.POST)

            # Verificar se os campos estão vazios e usar os valores dos campos personalizados
            if not form.instance.valor_documento and "valor_bruto" in self.request.POST:
                valor_bruto = self.request.POST.get("valor_bruto", "0")
                logger.info("Usando valor_bruto do POST: %s", valor_bruto)
                form.instance.valor_documento = Decimal(valor_bruto)

            if not form.instance.valor_iss and "valor_iss" in self.request.POST:
                valor_iss = self.request.POST.get("valor_iss", "0")
                logger.info("Usando valor_iss do POST: %s", valor_iss)
                form.instance.valor_iss = Decimal(valor_iss)

            if not form.instance.valor_irrf and "valor_irrf" in self.request.POST:
                valor_irrf = self.request.POST.get("valor_irrf", "0")
                logger.info("Usando valor_irrf do POST: %s", valor_irrf)
                form.instance.valor_irrf = Decimal(valor_irrf)

            if not form.instance.valor_liquido and "valor_liquido" in self.request.POST:
                valor_liquido = self.request.POST.get("valor_liquido", "0")
                logger.info("Usando valor_liquido do POST: %s", valor_liquido)
                form.instance.valor_liquido = Decimal(valor_liquido)

            # Garantir que a data e o status estejam preenchidos
            if (
                "data_documento" in self.request.POST
                and self.request.POST["data_documento"]
            ):
                logger.info(
                    "Data do documento do POST: %s", self.request.POST["data_documento"]
                )
            else:
                # Manter a data original se não for fornecida
                documento = self.get_object()
                form.instance.data_documento = documento.data_documento
                logger.info("Mantendo data original: %s", form.instance.data_documento)

            if "status" in self.request.POST and self.request.POST["status"]:
                logger.info(
                    "Status do documento do POST: %s", self.request.POST["status"]
                )
            else:
                # Manter o status original se não for fornecido
                documento = self.get_object()
                form.instance.status = documento.status
                logger.info("Mantendo status original: %s", form.instance.status)

            # Log dos valores finais antes de salvar
            logger.info("Valores finais antes de salvar:")
            logger.info("valor_documento: %s", form.instance.valor_documento)
            logger.info("valor_iss: %s", form.instance.valor_iss)
            logger.info("valor_irrf: %s", form.instance.valor_irrf)
            logger.info("valor_liquido: %s", form.instance.valor_liquido)
            logger.info("data_documento: %s", form.instance.data_documento)
            logger.info("status: %s", form.instance.status)

            logger.info("Chamando super().form_valid(form)")
            return super().form_valid(form)
        except ValidationError as e:
            logger.error("Erro de validação ao salvar formulário de edição: %s", e)
            messages.error(self.request, f"Erro de validação: {e}")
            return super().form_invalid(form)
        except ValueError as e:
            logger.error("Erro de valor ao salvar formulário de edição: %s", e)
            messages.error(self.request, f"Erro de valor: {e}")
            return super().form_invalid(form)
        except (TypeError, AttributeError) as e:
            logger.error("Erro de tipo ao salvar formulário de edição: %s", e)
            logger.error(traceback.format_exc())
            messages.error(self.request, f"Erro de tipo: {e}")
            return super().form_invalid(form)
        except (
            Exception
        ) as e:  # Mantido para capturar erros inesperados, mas com log detalhado
            logger.error("Erro inesperado ao salvar formulário de edição: %s", e)
            logger.error(traceback.format_exc())
            messages.error(self.request, f"Erro inesperado: {e}")
            return super().form_invalid(form)

    def form_invalid(self, form):
        """Processa o formulário de edição quando inválido e exibe mensagens de erro."""
        # Registrar erros no log
        logger.error("Erros de validação do formulário de edição: %s", form.errors)
        # Adicionar mensagens de erro para o usuário
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Erro no campo {field}: {error}")
        return super().form_invalid(form)


# A função buscar_fornecedor foi movida para api.py
# Agora estamos usando a função importada buscar_fornecedor_por_cnpj_cpf
buscar_fornecedor = buscar_fornecedor_por_cnpj_cpf


class DocumentoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Remove um documento financeiro com validação de permissões."""

    def get_success_url(self):
        """Retorna a URL para redirecionamento após exclusão bem-sucedida"""
        return self.success_url

    def delete(self, request, *args, **kwargs):
        """
        Sobrescreve o método delete para adicionar logs e tratamento de erros
        """
        try:
            logger.info("Tentando excluir documento com ID: %s", kwargs.get("pk"))
            response = super().delete(request, *args, **kwargs)
            messages.success(request, "Documento excluído com sucesso")
            return response
        except (PermissionError, OSError) as e:
            logger.error("Erro ao excluir documento: %s", str(e))
            messages.error(request, "Erro ao excluir documento")
            return redirect("documentos:list")

    model = Documento
    permission_required = "documentos.delete_documento"
    success_url = reverse_lazy("documentos:list")
    template_name = "documentos/documento_confirm_delete.html"


class DarBaixaDocumentoView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Realiza a baixa de um documento financeiro, alterando seu status para pago."""

    permission_required = "documentos.dar_baixa_documento"
    template_name = "documentos/dar_baixa_form.html"

    def get(self, request, pk):
        """Exibe o formulário para dar baixa no documento."""
        documento = get_object_or_404(Documento, pk=pk)
        if documento.status != "PEN":
            messages.error(request, "Este documento não pode ser baixado.")
            return redirect("documentos:detail", pk=pk)

        form = DarBaixaForm(initial={"data_pagamento": date.today()})
        return render(
            request, self.template_name, {"form": form, "documento": documento}
        )

    def post(self, request, pk):
        """Processa a requisição POST para dar baixa em um documento."""
        documento = get_object_or_404(Documento, pk=pk)
        form = DarBaixaForm(request.POST)

        if documento.status != "PEN":
            messages.error(request, "Este documento não pode ser baixado.")
            return redirect("documentos:detail", pk=pk)

        if form.is_valid():
            try:
                # Atualizar o status e as datas
                documento.status = "PAG"
                documento.data_pagamento = form.cleaned_data["data_pagamento"]
                documento.data_baixa = timezone.now()
                documento.baixado_por = request.user
                documento.save()

                logger.info(
                    "Documento %s baixado por %s. Data de pagamento: %s, Data da baixa: %s",
                    documento.numero,
                    request.user.username,
                    documento.data_pagamento,
                    documento.data_baixa,
                )

                messages.success(request, "Documento baixado com sucesso!")
                return redirect("documentos:detail", pk=pk)
            except ValidationError as e:
                logger.error("Erro ao dar baixa no documento: %s", e)
                messages.error(request, f"Erro ao dar baixa: {e}")

        # Se o formulário não for válido ou ocorrer um erro
        return render(
            request, self.template_name, {"form": form, "documento": documento}
        )


def dashboard(request):
    """
    Exibe o painel de controle com estatísticas de documentos financeiros.

    Mostra totais de documentos pendentes, pagos e atrasados, bem como
    valores financeiros e os últimos documentos registrados.
    """
    # Remover variável não utilizada
    # hoje = date.today()

    # Consultas otimizadas
    total_pendentes = Documento.objects.filter(status="PEN").count()
    total_pagos = Documento.objects.filter(status="PAG").count()
    total_atrasados = Documento.objects.filter(status="ATR").count()
    valor_pendente = (
        Documento.objects.filter(status="PEN").aggregate(total=Sum("valor_liquido"))[
            "total"
        ]
        or 0
    )
    valor_pago = (
        Documento.objects.filter(status="PAG").aggregate(total=Sum("valor_liquido"))[
            "total"
        ]
        or 0
    )
    ultimos_documentos = Documento.objects.order_by("-data_documento")[:5]

    context = {
        "total_pendentes": total_pendentes,
        "total_pagos": total_pagos,
        "total_atrasados": total_atrasados,
        "valor_pendente": valor_pendente,
        "valor_pago": valor_pago,
        "ultimos_documentos": ultimos_documentos,
    }

    return render(request, "documentos/dashboard.html", context)
