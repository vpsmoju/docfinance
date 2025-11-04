# pylint: disable=no-member
# # Importações da biblioteca padrão Python
import csv
import datetime
import logging
from decimal import Decimal
from io import BytesIO

# Importações de terceiros
import xlsxwriter

# Importações do Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

# Importações locais
from documentos.models import Documento, Secretaria, Recurso
from fornecedores.models import Fornecedor

# Configuração de logging
# Configuração do logger
logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """Dashboard principal com resumo de todos os relatórios"""
    # Contagem de documentos por status
    status_counts = {
        "pendentes": Documento.objects.filter(status="PEN").count(),
        "pagos": Documento.objects.filter(status="PAG").count(),
        "atrasados": Documento.objects.filter(status="ATR").count(),
    }

    # Valores totais
    valores_totais = {
        "bruto": Documento.objects.aggregate(total=Sum("valor_documento"))["total"]
        or 0,
        "liquido": Documento.objects.aggregate(total=Sum("valor_liquido"))["total"]
        or 0,
    }

    # Documentos por secretaria (top 5)
    docs_por_secretaria = (
        Documento.objects.values("secretaria")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Documentos por recurso (top 5)
    docs_por_recurso = (
        Documento.objects.values("recurso")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    context = {
        "status_counts": status_counts,
        "valores_totais": valores_totais,
        "docs_por_secretaria": docs_por_secretaria,
        "docs_por_recurso": docs_por_recurso,
    }

    return render(request, "relatorios/dashboard.html", context)


@login_required
def relatorio_fornecedores(request):
    """Relatório de Fornecedores com listagem em ordem alfabética"""
    search = request.GET.get("search", "").strip()

    queryset = Fornecedor.objects.all()

    if search:
        # Remover pontuações para busca por CNPJ/CPF
        digits = "".join(filter(str.isdigit, search))
        if digits:
            queryset = queryset.filter(Q(nome__icontains=search) | Q(cnpj_cpf__icontains=digits))
        else:
            queryset = queryset.filter(Q(nome__icontains=search))

    fornecedores = queryset.order_by("nome")

    context = {
        "fornecedores": fornecedores,
    }

    return render(request, "relatorios/relatorio_fornecedores.html", context)


@login_required
def relatorio_secretaria(request):
    """Relatório detalhado por secretaria"""
    secretaria = request.GET.get("secretaria", "")

    # Agrupamento por secretaria
    secretarias = (
        Documento.objects.select_related("secretaria")
        .values("secretaria", nome=F("secretaria__nome"))
        .annotate(
            count=Count("id"),
            valor_total=Sum("valor_documento"),
            valor_liquido=Sum("valor_liquido"),
        )
        .order_by("nome")
    )

    # Lista de documentos filtrados por secretaria
    if secretaria:
        documentos_list = Documento.objects.filter(
            secretaria_id=secretaria
        ).select_related("fornecedor", "secretaria")
        secretaria_nome = (
            Secretaria.objects.filter(pk=secretaria).values_list("nome", flat=True).first()
            or "Não definido"
        )
    else:
        documentos_list = Documento.objects.all().select_related("fornecedor")
        secretaria_nome = "Todas"

    # Paginação
    page = request.GET.get("page", 1)
    paginator = Paginator(documentos_list, 20)  # 20 documentos por página

    try:
        documentos = paginator.page(page)
    except PageNotAnInteger:
        documentos = paginator.page(1)
    except EmptyPage:
        documentos = paginator.page(paginator.num_pages)

    context = {
        "secretarias": secretarias,
        "documentos": documentos,
        "secretaria_selecionada": secretaria,
        "secretaria_nome": secretaria_nome,
        "secretaria_choices": [(s.id, s.nome) for s in Secretaria.objects.order_by("nome")],
        "is_paginated": True,
        "paginator": paginator,
    }

    return render(request, "relatorios/relatorio_secretaria.html", context)


@login_required
def relatorio_recurso(request):
    """Relatório detalhado por recurso"""
    recurso = request.GET.get("recurso", "")

    # Agrupamento por recurso
    recursos = (
        Documento.objects.select_related("recurso")
        .values("recurso", nome=F("recurso__nome"))
        .annotate(
            count=Count("id"),
            valor_total=Sum("valor_documento"),
            valor_liquido=Sum("valor_liquido"),
        )
        .order_by("nome")
    )

    # Lista de documentos filtrados por recurso
    if recurso:
        documentos_list = Documento.objects.filter(recurso_id=recurso).select_related(
            "fornecedor", "recurso"
        )
        recurso_nome = (
            Recurso.objects.filter(pk=recurso).values_list("nome", flat=True).first()
            or "Não definido"
        )
    else:
        documentos_list = Documento.objects.all().select_related("fornecedor")
        recurso_nome = "Todos"

    # Paginação
    page = request.GET.get("page", 1)
    paginator = Paginator(documentos_list, 20)  # 20 documentos por página

    try:
        documentos = paginator.page(page)
    except PageNotAnInteger:
        documentos = paginator.page(1)
    except EmptyPage:
        documentos = paginator.page(paginator.num_pages)

    context = {
        "recursos": recursos,
        "documentos": documentos,
        "recurso_selecionado": recurso,
        "recurso_nome": recurso_nome,
        "recurso_choices": [(r.id, r.nome) for r in Recurso.objects.order_by("nome")],
        "is_paginated": True,
        "paginator": paginator,
    }

    return render(request, "relatorios/relatorio_recurso.html", context)


def _agrupar_documentos(
    queryset, campo_agrupamento, titulo_agrupamento, choices=None, trunc_function=None
):
    """Função utilitária para agrupar documentos e calcular totais."""
    if trunc_function:
        agrupamentos = (
            queryset.annotate(agrupamento=trunc_function(campo_agrupamento))
            .values("agrupamento")
            .annotate(
                total_documentos=Count("id"),
                valor_total=Sum("valor_documento"),
                valor_pago=Sum(
                    Case(
                        When(status="PAG", then=F("valor_documento")),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
                valor_pendente=Sum(
                    Case(
                        When(status="PEN", then=F("valor_documento")),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
            )
            .order_by("agrupamento")
        )
    else:
        agrupamentos = (
            queryset.values(campo_agrupamento)
            .annotate(
                total_documentos=Count("id"),
                valor_total=Sum("valor_documento"),
                valor_pago=Sum(
                    Case(
                        When(status="PAG", then=F("valor_documento")),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
                valor_pendente=Sum(
                    Case(
                        When(status="PEN", then=F("valor_documento")),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
            )
            .order_by(campo_agrupamento)
        )

    total_valor_geral = queryset.aggregate(total=Sum("valor_documento"))["total"] or 0
    resumo = []
    for item in agrupamentos:
        nome_agrupamento = (
            item.get("agrupamento") if trunc_function else item.get(campo_agrupamento)
        )
        nome = nome_agrupamento
        if choices and nome in dict(choices):
            nome = dict(choices).get(nome, "Não definido")
        elif trunc_function and nome:
            nome = nome.strftime("%B/%Y")
        elif nome is None:
            nome = "Não definido"

        resumo.append(
            {
                "nome": nome,
                "total_documentos": item["total_documentos"],
                "valor_total": item["valor_total"] or 0,
                "valor_pago": item["valor_pago"] or 0,
                "valor_pendente": item["valor_pendente"] or 0,
                "percentual": (item["valor_total"] / total_valor_geral * 100)
                if total_valor_geral
                else 0,
            }
        )
    return titulo_agrupamento, resumo


@login_required
def relatorio_financeiro(request):
    """Relatório financeiro com filtros por período (corrigido)"""
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    status = request.GET.get("status", "")
    tipo_agrupamento = request.GET.get("tipo_agrupamento", "mes")

    filtros = Q()

    if data_inicio:
        try:
            data_inicio = datetime.datetime.strptime(data_inicio, "%Y-%m-%d")
            filtros &= Q(data_documento__gte=data_inicio)
        except ValueError:
            logger.error("Formato de data inválido para data_inicio: %s", data_inicio)

    if data_fim:
        try:
            data_fim = datetime.datetime.strptime(data_fim, "%Y-%m-%d")
            filtros &= Q(data_documento__lte=data_fim)
        except ValueError:
            logger.error("Formato de data inválido para data_fim: %s", data_fim)

    if status:
        filtros &= Q(status=status)

    documentos = Documento.objects.filter(filtros).select_related("fornecedor")

    context = {
        "documentos": documentos,
        "total_documentos": documentos.count(),
        "total_valor": documentos.aggregate(total=Sum("valor_documento"))["total"] or 0,
        "total_pago": documentos.filter(status="PAG").aggregate(
            total=Sum("valor_documento")
        )["total"]
        or 0,
        "total_pendente": documentos.filter(status="PEN").aggregate(
            total=Sum("valor_documento")
        )["total"]
        or 0,
        "tipo_agrupamento": tipo_agrupamento,
    }

    if tipo_agrupamento == "mes":
        context["agrupamento_titulo"], context["resumo_financeiro"] = (
            _agrupar_documentos(
                documentos, "data_documento", "Mês", trunc_function=TruncMonth
            )
        )
    elif tipo_agrupamento == "secretaria":
        context["agrupamento_titulo"], context["resumo_financeiro"] = (
            _agrupar_documentos(
                documentos, "secretaria", "Secretaria", [(s.id, s.nome) for s in Secretaria.objects.all()]
            )
        )
    elif tipo_agrupamento == "recurso":
        context["agrupamento_titulo"], context["resumo_financeiro"] = (
            _agrupar_documentos(
                documentos, "recurso", "Recurso", [(r.id, r.nome) for r in Recurso.objects.all()]
            )
        )
    else:
        context["agrupamento_titulo"], context["resumo_financeiro"] = (
            _agrupar_documentos(
                documentos,
                "data_documento",
                "Mês",
                trunc_function=TruncMonth,  # Default
            )
        )

    return render(request, "relatorios/relatorio_financeiro.html", context)


@login_required
def relatorio_pagamentos(request):
    """Relatório de pagamentos agrupado por secretaria e recurso"""
    # Obter parâmetros de filtro
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    status = request.GET.get("status", "")
    secretaria = request.GET.get("secretaria", "")

    # Converter strings para objetos datetime
    if data_inicio:
        data_inicio = datetime.datetime.strptime(data_inicio, "%Y-%m-%d")
    else:
        # Padrão: início do mês atual
        hoje = timezone.now()
        data_inicio = datetime.datetime(hoje.year, hoje.month, 1)

    if data_fim:
        data_fim = datetime.datetime.strptime(data_fim, "%Y-%m-%d")
        # Ajustar para o final do dia
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
    else:
        # Padrão: data atual
        data_fim = timezone.now()

    # Filtrar documentos pelo período
    documentos = Documento.objects.filter(
        data_documento__gte=data_inicio, data_documento__lte=data_fim
    ).select_related("fornecedor")

    # Aplicar filtro de status se fornecido
    if status:
        documentos = documentos.filter(status=status)

    # Filtrar por secretaria se fornecido
    if secretaria:
        documentos = documentos.filter(secretaria_id=secretaria)
        secretaria_nome = (
            Secretaria.objects.filter(pk=secretaria).values_list("nome", flat=True).first()
            or "Não definido"
        )
    else:
        secretaria_nome = "Todas"

    # Agrupar por secretaria
    secretarias_dados = {}
    total_geral = {
        "quantidade": 0,
        "total": Decimal("0.00"),
        "total_liquido": Decimal("0.00"),
        "total_iss": Decimal("0.00"),
        "total_irrf": Decimal("0.00"),
    }

    # Processar cada secretaria
    for s in Secretaria.objects.order_by("nome"):
        # Filtrar documentos por secretaria
        docs_secretaria = documentos.filter(secretaria=s)

        if docs_secretaria.exists():
            # Calcular totais da secretaria
            total_secretaria = docs_secretaria.aggregate(
                total=Sum("valor_documento"),
                total_liquido=Sum("valor_liquido"),
                total_iss=Sum("valor_iss"),
                total_irrf=Sum("valor_irrf"),
                quantidade=Count("id"),
            )

            # Agrupar por recurso dentro da secretaria
            recursos_dados = []

            # Obter recursos para esta secretaria dinamicamente
            recursos_choices = Recurso.objects.filter(secretaria=s).order_by("nome")

            for recurso in recursos_choices:
                # Filtrar documentos por recurso
                docs_recurso = docs_secretaria.filter(recurso=recurso)

                if docs_recurso.exists():
                    # Calcular totais do recurso
                    total_recurso = docs_recurso.aggregate(
                        total=Sum("valor_documento"),
                        total_liquido=Sum("valor_liquido"),
                        total_iss=Sum("valor_iss"),
                        total_irrf=Sum("valor_irrf"),
                        quantidade=Count("id"),
                    )

                    # Adicionar dados do recurso
                    recursos_dados.append(
                        {
                            "recurso_code": recurso.id,
                            "recurso_nome": recurso.nome,
                            "total": total_recurso["total"],
                            "total_liquido": total_recurso["total_liquido"],
                            "total_iss": total_recurso["total_iss"],
                            "total_irrf": total_recurso["total_irrf"],
                            "quantidade": total_recurso["quantidade"],
                            "documentos": docs_recurso,
                        }
                    )

            # Adicionar dados da secretaria
            secretarias_dados[s.id] = {
                "secretaria_nome": s.nome,
                "total": total_secretaria["total"],
                "total_liquido": total_secretaria["total_liquido"],
                "total_iss": total_secretaria["total_iss"],
                "total_irrf": total_secretaria["total_irrf"],
                "quantidade": total_secretaria["quantidade"],
                "recursos": recursos_dados,
            }

            # Atualizar totais gerais
            total_geral["quantidade"] += total_secretaria["quantidade"]
            total_geral["total"] += total_secretaria["total"] or Decimal("0.00")
            total_geral["total_liquido"] += total_secretaria[
                "total_liquido"
            ] or Decimal("0.00")
            total_geral["total_iss"] += total_secretaria["total_iss"] or Decimal("0.00")
            total_geral["total_irrf"] += total_secretaria["total_irrf"] or Decimal(
                "0.00"
            )

    # Verificar se foi solicitada exportação
    formato = request.GET.get("formato", "")
    if formato:
        return exportar_pagamentos(request, secretarias_dados, total_geral, formato)

    context = {
        "secretarias_dados": secretarias_dados,
        "total_geral": total_geral,
        "secretaria_selecionada": secretaria,
        "secretaria_nome": secretaria_nome,
        "secretaria_choices": [(sec.id, sec.nome) for sec in Secretaria.objects.order_by("nome")],
        "data_inicio": data_inicio.strftime("%Y-%m-%d"),
        "data_fim": data_fim.strftime("%Y-%m-%d"),
        "status_selecionado": status,
    }

    return render(request, "relatorios/relatorio_pagamentos.html", context)


def exportar_pagamentos(_, secretarias_dados, total_geral, formato):
    """Exporta o relatório de pagamentos para CSV ou Excel"""
    try:
        if formato == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                'attachment; filename="relatorio_pagamentos.csv"'
            )

            writer = csv.writer(response)
            writer.writerow(
                [
                    "Secretaria",
                    "Recurso",
                    "Fornecedor",
                    "Descrição",
                    "Valor Bruto",
                    "ISS",
                    "IR",
                    "Valor Líquido",
                ]
            )

            # Para a linha 550
            for _, secretaria_data in secretarias_dados.items():
                for recurso_data in secretaria_data["recursos"]:
                    for doc in recurso_data["documentos"]:
                        try:
                            writer.writerow(
                                [
                                    secretaria_data["secretaria_nome"],
                                    recurso_data["recurso_nome"],
                                    doc.fornecedor.nome
                                    if doc.fornecedor
                                    else "Sem fornecedor",
                                    doc.descricao or "",
                                    doc.valor_documento,
                                    doc.valor_iss,
                                    doc.valor_irrf,
                                    doc.valor_liquido,
                                ]
                            )
                        except AttributeError as e:
                            # Log do erro e continua com o próximo documento
                            logger.error("Erro ao processar documento para CSV: %s", e)
                            continue

            return response
        elif formato == "excel":
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # Formatos
            titulo = workbook.add_format({"bold": True, "font_size": 14})
            cabecalho = workbook.add_format({"bold": True, "bg_color": "#CCCCCC"})
            moeda = workbook.add_format({"num_format": "R$ #,##0.00"})

            # Título
            worksheet.write(0, 0, "Relatório de Pagamentos", titulo)
            worksheet.write(1, 0, f"Total de documentos: {total_geral['quantidade']}")
            worksheet.write(2, 0, f"Valor total: R$ {total_geral['total']:,.2f}")

            # Cabeçalhos
            headers = [
                "Secretaria",
                "Recurso",
                "Fornecedor",
                "Descrição",
                "Valor Bruto",
                "ISS",
                "IR",
                "Valor Líquido",
            ]
            for col, header in enumerate(headers):
                worksheet.write(4, col, header, cabecalho)

            # Dados
            row = 5
            # Corrigindo a iteração dos dados
            for _, secretaria_data in secretarias_dados.items():
                for recurso_data in secretaria_data["recursos"]:
                    for doc in recurso_data["documentos"]:
                        try:
                            worksheet.write(row, 0, secretaria_data["secretaria_nome"])
                            worksheet.write(row, 1, recurso_data["recurso_nome"])
                            worksheet.write(
                                row,
                                2,
                                doc.fornecedor.nome
                                if doc.fornecedor
                                else "Sem fornecedor",
                            )
                            worksheet.write(row, 3, doc.descricao or "")
                            worksheet.write(row, 4, doc.valor_documento, moeda)
                            worksheet.write(row, 5, doc.valor_iss, moeda)
                            worksheet.write(row, 6, doc.valor_irrf, moeda)
                            worksheet.write(row, 7, doc.valor_liquido, moeda)
                            row += 1
                        except AttributeError as e:
                            # Log do erro e continua com o próximo documento
                            logger.error("Erro ao processar documento: %s", e)

            # Ajustar largura das colunas
            worksheet.set_column(0, 0, 25)  # Secretaria
            worksheet.set_column(1, 1, 20)  # Recurso
            worksheet.set_column(2, 2, 30)  # Fornecedor
            worksheet.set_column(3, 3, 40)  # Descrição
            worksheet.set_column(4, 7, 15)  # Valores

            workbook.close()

            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                'attachment; filename="relatorio_pagamentos.xlsx"'
            )
            return response

        else:
            # Tratamento para formato não suportado
            return HttpResponse(
                "Formato não suportado", content_type="text/plain", status=400
            )
    except (OSError, xlsxwriter.XlsxWriter.exceptions.XlsxWriterException) as e:
        # Tratamento de erro geral
        logger.error("Erro ao exportar relatório: %s", e)
        return HttpResponse(
            f"Erro ao gerar relatório: {str(e)}", content_type="text/plain", status=500
        )


@login_required
def filtro_encaminhamento(request):
    """Filtro para selecionar documentos a serem encaminhados"""
    # Obter parâmetros do filtro
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    secretaria_id = request.GET.get("secretaria", "")
    fornecedor = request.GET.get("fornecedor", "")
    destino = request.GET.get("destino", "")  # controle_interno ou contabilidade

    # Inicializar queryset
    documentos = Documento.objects.all().order_by("fornecedor__nome", "data_documento")

    # Aplicar filtros
    if data_inicio:
        data_inicio = datetime.datetime.strptime(data_inicio, "%Y-%m-%d").date()
        documentos = documentos.filter(data_documento__gte=data_inicio)

    if data_fim:
        data_fim = datetime.datetime.strptime(data_fim, "%Y-%m-%d").date()
        documentos = documentos.filter(data_documento__lte=data_fim)

    if secretaria_id:
        documentos = documentos.filter(secretaria_id=secretaria_id)

    if fornecedor:
        documentos = documentos.filter(fornecedor__nome__icontains=fornecedor)

    # Paginação
    page = request.GET.get("page", 1)
    paginator = Paginator(documentos, 20)  # 20 documentos por página

    try:
        documentos_paginados = paginator.page(page)
    except PageNotAnInteger:
        documentos_paginados = paginator.page(1)
    except EmptyPage:
        documentos_paginados = paginator.page(paginator.num_pages)

    context = {
        "documentos": documentos_paginados,
        "secretarias": [(s.id, s.nome) for s in Secretaria.objects.order_by("nome")],
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "secretaria": secretaria_id,
        "fornecedor": fornecedor,
        "is_paginated": True,
        "paginator": paginator,
        "destino": destino,
    }

    return render(request, "relatorios/filtro_encaminhamento.html", context)


@login_required
def relatorio_encaminhamento(request):
    """Relatório de encaminhamentos para Controle Interno e Contabilidade"""
    # Usar timezone.now() em vez de datetime.now()
    data_atual = timezone.now().date()
    ano_atual = data_atual.year

    # Obter o tipo de encaminhamento (controle_interno ou contabilidade)
    tipo_encaminhamento = request.GET.get("tipo", "controle_interno")

    # Obter IDs dos documentos selecionados
    documentos_ids = request.GET.getlist("documentos")

    # Obter documentos selecionados
    if documentos_ids:
        documentos = Documento.objects.filter(id__in=documentos_ids).order_by(
            "fornecedor__nome", "data_documento"
        )
    else:
        # Se não houver documentos selecionados, redirecionar para a página de filtro
        return redirect("relatorios:filtro_encaminhamento")

    # Obter o número e ano do ofício
    numero_oficio = request.GET.get("numero_oficio", f"{documentos.count():03d}")
    ano_oficio = request.GET.get("ano_oficio", ano_atual)

    # Definir destinatário com base no tipo de encaminhamento
    if tipo_encaminhamento == "controle_interno":
        destinatario = "RODRIGO BASTOS DE LIMA"
        cargo_destinatario = "Controlador Municipal"
    else:  # contabilidade
        destinatario = "MARIA APARECIDA SILVA"
        cargo_destinatario = "Contadora Municipal"

    # Obter informações do secretário
    secretario_nome = "CARLOS EDUARDO ALVES DA SILVA"
    secretario_decreto = "008/2023"

    context = {
        "documentos": documentos,
        "tipo_encaminhamento": tipo_encaminhamento,
        "data_atual": data_atual,
        "ano_atual": ano_atual,
        "numero_oficio": numero_oficio,
        "ano_oficio": ano_oficio,
        "destinatario": destinatario,
        "cargo_destinatario": cargo_destinatario,
        "secretario_nome": secretario_nome,
        "secretario_decreto": secretario_decreto,
    }

    return render(request, "relatorios/relatorio_encaminhamento.html", context)


@login_required
def relatorio_contabilidade(request):
    """Relatório de encaminhamento para contabilidade"""
    # Obter IDs dos documentos selecionados
    documentos_ids = request.GET.getlist("documentos")

    if not documentos_ids:
        messages.warning(request, "Nenhum documento foi selecionado para o relatório.")
        return redirect("relatorios:filtro_encaminhamento")

    # Buscar documentos pelo ID
    documentos = Documento.objects.filter(id__in=documentos_ids).select_related(
        "fornecedor"
    )

    # Calcular valor total
    # Calculate total value and add to context
    total_valor = (
        documentos.aggregate(total_valor=Sum("valor_documento"))["total_valor"] or 0
    )
    # Add total value to the existing context dictionary
    context = {}
    if "total_valor" not in context:
        context = {}
    context["total_valor"] = total_valor

    # Adicionar numeração sequencial
    for i, doc in enumerate(documentos, 1):
        doc.numero_sequencial = i

    # Determinar a secretaria dos documentos
    # Assumindo que todos os documentos são da mesma secretaria, pegamos a primeira
    secretaria = None
    if documentos:
        primeiro_doc = documentos.first()
        secretaria = primeiro_doc.get_secretaria_display()

    context = {
        "documentos": documentos,
        "data_atual": datetime.datetime.now(),
        "secretaria": secretaria,
        "secretario_nome": "CARLOS EDUARDO ALVES DA SILVA",
        "secretario_decreto": "008/2023",
    }

    return render(request, "relatorios/relatorio_contabilidade.html", context)


@login_required
def exportar_csv(request):
    """Exporta relatórios para formato CSV"""
    tipo = request.GET.get("tipo", "documentos")

    # Obter parâmetros de filtro
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    status = request.GET.get("status", "")
    secretaria = request.GET.get("secretaria", "")
    recurso = request.GET.get("recurso", "")

    # Inicializar queryset
    documentos = Documento.objects.all().order_by("data_documento")

    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio = datetime.datetime.strptime(data_inicio, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__gte=data_inicio)
        except ValueError:
            pass

    if data_fim:
        try:
            data_fim = datetime.datetime.strptime(data_fim, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__lte=data_fim)
        except ValueError:
            pass

    if status:
        documentos = documentos.filter(status=status)

    if secretaria:
        documentos = documentos.filter(secretaria=secretaria)

    if recurso:
        documentos = documentos.filter(recurso=recurso)

    # Configurar resposta CSV
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="relatorio_{tipo}.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Fornecedor",
            "Descrição",
            "Data",
            "Valor",
            "Valor Líquido",
            "Secretaria",
            "Recurso",
            "Status",
        ]
    )

    for doc in documentos:
        writer.writerow(
            [
                doc.id,
                doc.fornecedor.nome if doc.fornecedor else "",
                doc.descricao or "",
                doc.data_documento.strftime("%d/%m/%Y") if doc.data_documento else "",
                doc.valor_documento,
                doc.valor_liquido,
                doc.get_secretaria_display(),
                doc.get_recurso_display(),
                doc.get_status_display(),
            ]
        )

    return response


@login_required
def exportar_excel(request):
    """Exporta relatórios para formato Excel"""
    tipo = request.GET.get("tipo", "documentos")

    # Obter parâmetros de filtro
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    status = request.GET.get("status", "")
    secretaria = request.GET.get("secretaria", "")
    recurso = request.GET.get("recurso", "")

    # Inicializar queryset
    documentos = Documento.objects.all().order_by("data_documento")

    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio = datetime.datetime.strptime(data_inicio, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__gte=data_inicio)
        except ValueError:
            pass

    if data_fim:
        try:
            data_fim = datetime.datetime.strptime(data_fim, "%Y-%m-%d").date()
            documentos = documentos.filter(data_documento__lte=data_fim)
        except ValueError:
            pass

    if status:
        documentos = documentos.filter(status=status)

    if secretaria:
        documentos = documentos.filter(secretaria=secretaria)

    if recurso:
        documentos = documentos.filter(recurso=recurso)

    # Configurar resposta Excel
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Formatos
    titulo = workbook.add_format({"bold": True, "font_size": 14})
    cabecalho = workbook.add_format({"bold": True, "bg_color": "#CCCCCC"})
    moeda = workbook.add_format({"num_format": "R$ #,##0.00"})
    data = workbook.add_format({"num_format": "dd/mm/yyyy"})

    # Título
    worksheet.write(0, 0, f"Relatório de {tipo.capitalize()}", titulo)
    worksheet.write(1, 0, f"Total de documentos: {documentos.count()}")

    # Cabeçalhos
    headers = [
        "ID",
        "Fornecedor",
        "Descrição",
        "Data",
        "Valor",
        "Valor Líquido",
        "Secretaria",
        "Recurso",
        "Status",
    ]
    for col, header in enumerate(headers):
        worksheet.write(3, col, header, cabecalho)

    # Dados
    for row, doc in enumerate(documentos, start=4):
        worksheet.write(row, 0, doc.id)
        worksheet.write(row, 1, doc.fornecedor.nome if doc.fornecedor else "")
        worksheet.write(row, 2, doc.descricao or "")
        if doc.data_documento:
            worksheet.write_datetime(row, 3, doc.data_documento, data)
        else:
            worksheet.write(row, 3, "")
        worksheet.write(row, 4, doc.valor_documento, moeda)
        worksheet.write(row, 5, doc.valor_liquido, moeda)
        worksheet.write(row, 6, doc.get_secretaria_display())
        worksheet.write(row, 7, doc.get_recurso_display())
        worksheet.write(row, 8, doc.get_status_display())

    # Ajustar largura das colunas
    worksheet.set_column(0, 0, 10)  # ID
    worksheet.set_column(1, 1, 30)  # Fornecedor
    worksheet.set_column(2, 2, 40)  # Descrição
    worksheet.set_column(3, 3, 15)  # Data
    worksheet.set_column(4, 5, 15)  # Valores
    worksheet.set_column(6, 7, 25)  # Secretaria/Recurso
    worksheet.set_column(8, 8, 15)  # Status

    workbook.close()

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="relatorio_{tipo}.xlsx"'

    return response


@login_required
def dados_grafico(_):
    """Return JSON data for dashboard charts"""
    # Get data from the dashboard function
    status_counts = {
        "pendentes": Documento.objects.filter(status="PEN").count(),
        "pagos": Documento.objects.filter(status="PAG").count(),
        "atrasados": Documento.objects.filter(status="ATR").count(),
    }

    # Documents by secretaria (top 5)
    docs_por_secretaria = (
        Documento.objects.values("secretaria")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Documents by recurso (top 5)
    docs_por_recurso = (
        Documento.objects.values("recurso")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Format data for charts
    data = {
        "status": {
            "labels": ["Pendentes", "Pagos", "Atrasados"],
            "data": [
                status_counts["pendentes"],
                status_counts["pagos"],
                status_counts["atrasados"],
            ],
            "colors": ["#ffc107", "#28a745", "#dc3545"],
        },
        "secretarias": {
            "labels": [doc["secretaria"] for doc in docs_por_secretaria],
            "data": [doc["count"] for doc in docs_por_secretaria],
        },
        "recursos": {
            "labels": [doc["recurso"] for doc in docs_por_recurso],
            "data": [doc["count"] for doc in docs_por_recurso],
        },
    }

    return JsonResponse(data)
