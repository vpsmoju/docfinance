import csv
import io
from datetime import datetime

import xlsxwriter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView

from .models import Documento


class RelatorioBaseView(LoginRequiredMixin, TemplateView):
    """Classe base para todos os relatórios"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtros de data
        data_inicio = self.request.GET.get("data_inicio")
        data_fim = self.request.GET.get("data_fim")

        # Converter strings para objetos datetime
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        else:
            # Padrão: início do mês atual
            hoje = timezone.now()
            data_inicio = datetime(hoje.year, hoje.month, 1)

        if data_fim:
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            # Ajustar para o final do dia
            data_fim = data_fim.replace(hour=23, minute=59, second=59)
        else:
            # Padrão: data atual
            data_fim = timezone.now()

        # Adicionar datas ao contexto
        context["data_inicio"] = data_inicio.strftime("%Y-%m-%d")
        context["data_fim"] = data_fim.strftime("%Y-%m-%d")

        # Filtro de status
        status = self.request.GET.get("status", "")
        context["status_selecionado"] = status

        # Filtrar documentos pelo período
        documentos = Documento.objects.filter(
            data_documento__gte=data_inicio, data_documento__lte=data_fim
        )

        # Aplicar filtro de status se fornecido
        if status:
            documentos = documentos.filter(status=status)

        context["documentos"] = documentos
        return context


class RelatorioSecretariaView(RelatorioBaseView):
    """Relatório agrupado por secretaria"""

    template_name = "relatorios/relatorio_secretaria.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documentos = context["documentos"]

        # Agrupar por secretaria
        secretarias_dados = (
            documentos.values("secretaria")
            .annotate(
                total=Sum("valor_documento"),
                total_liquido=Sum("valor_liquido"),
                quantidade=Count("id"),
            )
            .order_by("secretaria")
        )

        # Adicionar nome legível da secretaria
        for item in secretarias_dados:
            for choice in Documento.SECRETARIA_CHOICES:
                if choice[0] == item["secretaria"]:
                    item["secretaria_nome"] = choice[1]
                    break
            else:
                item["secretaria_nome"] = "Não definido"

        context["secretarias_dados"] = secretarias_dados
        context["total_geral"] = documentos.aggregate(
            total=Sum("valor_documento"),
            total_liquido=Sum("valor_liquido"),
            quantidade=Count("id"),
        )

        # Formato de exportação
        context["formato"] = self.request.GET.get("formato", "")

        # Se solicitado exportação
        if context["formato"]:
            return self.exportar_dados(context)

        return context

    def exportar_dados(self, context):
        formato = context["formato"]
        secretarias_dados = context["secretarias_dados"]

        if formato == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                'attachment; filename="relatorio_secretarias.csv"'
            )

            writer = csv.writer(response)
            writer.writerow(
                ["Secretaria", "Quantidade", "Valor Total", "Valor Líquido"]
            )

            for item in secretarias_dados:
                writer.writerow(
                    [
                        item["secretaria_nome"],
                        item["quantidade"],
                        item["total"],
                        item["total_liquido"],
                    ]
                )

            return response

        elif formato == "excel":
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # Formatos
            titulo = workbook.add_format({"bold": True, "font_size": 14})
            cabecalho = workbook.add_format({"bold": True, "bg_color": "#CCCCCC"})
            moeda = workbook.add_format({"num_format": "R$ #,##0.00"})

            # Título
            worksheet.write(0, 0, "Relatório por Secretaria", titulo)
            worksheet.write(
                1, 0, f"Período: {context['data_inicio']} a {context['data_fim']}"
            )

            # Cabeçalhos
            headers = ["Secretaria", "Quantidade", "Valor Total", "Valor Líquido"]
            for col, header in enumerate(headers):
                worksheet.write(3, col, header, cabecalho)

            # Dados
            row = 4
            for item in secretarias_dados:
                worksheet.write(row, 0, item["secretaria_nome"])
                worksheet.write(row, 1, item["quantidade"])
                worksheet.write(row, 2, item["total"], moeda)
                worksheet.write(row, 3, item["total_liquido"], moeda)
                row += 1

            # Total
            worksheet.write(row + 1, 0, "TOTAL", cabecalho)
            worksheet.write(row + 1, 1, context["total_geral"]["quantidade"], cabecalho)
            worksheet.write(row + 1, 2, context["total_geral"]["total"], cabecalho)
            worksheet.write(
                row + 1, 3, context["total_geral"]["total_liquido"], cabecalho
            )

            # Ajustar largura das colunas
            worksheet.set_column(0, 0, 30)
            worksheet.set_column(1, 3, 15)

            workbook.close()

            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                'attachment; filename="relatorio_secretarias.xlsx"'
            )
            return response

        return context


class RelatorioRecursoView(RelatorioBaseView):
    """Relatório agrupado por recurso"""

    template_name = "relatorios/relatorio_recurso.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documentos = context["documentos"]

        # Agrupar por recurso
        recursos_dados = (
            documentos.values("recurso")
            .annotate(
                total=Sum("valor_documento"),
                total_liquido=Sum("valor_liquido"),
                quantidade=Count("id"),
            )
            .order_by("recurso")
        )

        # Adicionar nome legível do recurso
        for item in recursos_dados:
            for choice in Documento.RECURSO_CHOICES:
                if choice[0] == item["recurso"]:
                    item["recurso_nome"] = choice[1]
                    break
            else:
                item["recurso_nome"] = "Não definido"

        context["recursos_dados"] = recursos_dados
        context["total_geral"] = documentos.aggregate(
            total=Sum("valor_documento"),
            total_liquido=Sum("valor_liquido"),
            quantidade=Count("id"),
        )

        # Formato de exportação
        context["formato"] = self.request.GET.get("formato", "")

        # Se solicitado exportação
        if context["formato"]:
            return self.exportar_dados(context)

        return context

    def exportar_dados(self, context):
        formato = context["formato"]
        recursos_dados = context["recursos_dados"]

        if formato == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                'attachment; filename="relatorio_recursos.csv"'
            )

            writer = csv.writer(response)
            writer.writerow(["Recurso", "Quantidade", "Valor Total", "Valor Líquido"])

            for item in recursos_dados:
                writer.writerow(
                    [
                        item["recurso_nome"],
                        item["quantidade"],
                        item["total"],
                        item["total_liquido"],
                    ]
                )

            return response

        elif formato == "excel":
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()

            # Formatos
            titulo = workbook.add_format({"bold": True, "font_size": 14})
            cabecalho = workbook.add_format({"bold": True, "bg_color": "#CCCCCC"})
            moeda = workbook.add_format({"num_format": "R$ #,##0.00"})

            # Título
            worksheet.write(0, 0, "Relatório por Recurso", titulo)
            worksheet.write(
                1, 0, f"Período: {context['data_inicio']} a {context['data_fim']}"
            )

            # Cabeçalhos
            headers = ["Recurso", "Quantidade", "Valor Total", "Valor Líquido"]
            for col, header in enumerate(headers):
                worksheet.write(3, col, header, cabecalho)

            # Dados
            row = 4
            for item in recursos_dados:
                worksheet.write(row, 0, item["recurso_nome"])
                worksheet.write(row, 1, item["quantidade"])
                worksheet.write(row, 2, item["total"], moeda)
                worksheet.write(row, 3, item["total_liquido"], moeda)
                row += 1

            # Total
            worksheet.write(row + 1, 0, "TOTAL", cabecalho)
            worksheet.write(row + 1, 1, context["total_geral"]["quantidade"], cabecalho)
            worksheet.write(row + 1, 2, context["total_geral"]["total"], cabecalho)
            worksheet.write(
                row + 1, 3, context["total_geral"]["total_liquido"], cabecalho
            )

            # Ajustar largura das colunas
            worksheet.set_column(0, 0, 30)
            worksheet.set_column(1, 3, 15)

            workbook.close()

            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                'attachment; filename="relatorio_recursos.xlsx"'
            )
            return response

        return context


class RelatorioFinanceiroView(RelatorioBaseView):
    """Relatório financeiro com análise de valores"""

    template_name = "relatorios/relatorio_financeiro.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documentos = context["documentos"]

        # Resumo financeiro
        resumo = {
            "total_bruto": documentos.aggregate(total=Sum("valor_documento"))["total"]
            or 0,
            "total_iss": documentos.aggregate(total=Sum("valor_iss"))["total"] or 0,
            "total_irrf": documentos.aggregate(total=Sum("valor_irrf"))["total"] or 0,
            "total_liquido": documentos.aggregate(total=Sum("valor_liquido"))["total"]
            or 0,
            "quantidade": documentos.count(),
            "pendentes": documentos.filter(status="PEN").count(),
            "pagos": documentos.filter(status="PAG").count(),
            "atrasados": documentos.filter(status="ATR").count(),
        }

        # Adicionar percentuais
        if resumo["quantidade"] > 0:
            resumo["perc_pendentes"] = (
                resumo["pendentes"] / resumo["quantidade"]
            ) * 100
            resumo["perc_pagos"] = (resumo["pagos"] / resumo["quantidade"]) * 100
            resumo["perc_atrasados"] = (
                resumo["atrasados"] / resumo["quantidade"]
            ) * 100
        else:
            resumo["perc_pendentes"] = resumo["perc_pagos"] = resumo[
                "perc_atrasados"
            ] = 0

        context["resumo"] = resumo

        # Dados para gráficos
        context["dados_grafico"] = {
            "labels": ["Pendentes", "Pagos", "Atrasados"],
            "valores": [resumo["pendentes"], resumo["pagos"], resumo["atrasados"]],
            "cores": ["#ffc107", "#28a745", "#dc3545"],
        }

        # Formato de exportação
        context["formato"] = self.request.GET.get("formato", "")

        # Se solicitado exportação
        if context["formato"]:
            return self.exportar_dados(context)

        return context

    def exportar_dados(self, context):
        formato = context["formato"]
        resumo = context["resumo"]
        documentos = context["documentos"]

        if formato == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                'attachment; filename="relatorio_financeiro.csv"'
            )

            writer = csv.writer(response)
            writer.writerow(
                [
                    "Número",
                    "Fornecedor",
                    "Data",
                    "Valor Bruto",
                    "ISS",
                    "IRRF",
                    "Valor Líquido",
                    "Status",
                ]
            )

            for doc in documentos:
                status_texto = "Pendente"
                if doc.status == "PAG":
                    status_texto = "Pago"
                elif doc.status == "ATR":
                    status_texto = "Atrasado"

                writer.writerow(
                    [
                        doc.numero,
                        doc.fornecedor,
                        doc.data_documento.strftime("%d/%m/%Y"),
                        doc.valor_documento,
                        doc.valor_iss,
                        doc.valor_irrf,
                        doc.valor_liquido,
                        status_texto,
                    ]
                )

            # Adicionar resumo
            writer.writerow([])
            writer.writerow(["RESUMO"])
            writer.writerow(["Total Bruto", resumo["total_bruto"]])
            writer.writerow(["Total ISS", resumo["total_iss"]])
            writer.writerow(["Total IRRF", resumo["total_irrf"]])
            writer.writerow(["Total Líquido", resumo["total_liquido"]])
            writer.writerow(["Quantidade", resumo["quantidade"]])
            writer.writerow(["Pendentes", resumo["pendentes"]])
            writer.writerow(["Pagos", resumo["pagos"]])
            writer.writerow(["Atrasados", resumo["atrasados"]])

            return response

        elif formato == "excel":
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet("Detalhes")
            resumo_sheet = workbook.add_worksheet("Resumo")

            # Formatos
            titulo = workbook.add_format({"bold": True, "font_size": 14})
            cabecalho = workbook.add_format({"bold": True, "bg_color": "#CCCCCC"})
            moeda = workbook.add_format({"num_format": "R$ #,##0.00"})
            data_format = workbook.add_format({"num_format": "dd/mm/yyyy"})

            # Título
            worksheet.write(0, 0, "Relatório Financeiro", titulo)
            worksheet.write(
                1, 0, f"Período: {context['data_inicio']} a {context['data_fim']}"
            )

            # Cabeçalhos
            headers = [
                "Número",
                "Fornecedor",
                "Data",
                "Valor Bruto",
                "ISS",
                "IRRF",
                "Valor Líquido",
                "Status",
            ]
            for col, header in enumerate(headers):
                worksheet.write(3, col, header, cabecalho)

            # Dados
            row = 4
            for doc in documentos:
                status_texto = "Pendente"
                if doc.status == "PAG":
                    status_texto = "Pago"
                elif doc.status == "ATR":
                    status_texto = "Atrasado"

                worksheet.write(row, 0, doc.numero)
                worksheet.write(row, 1, doc.fornecedor)
                worksheet.write_datetime(row, 2, doc.data_documento, data_format)
                worksheet.write(row, 3, doc.valor_documento, moeda)
                worksheet.write(row, 4, doc.valor_iss, moeda)
                worksheet.write(row, 5, doc.valor_irrf, moeda)
                worksheet.write(row, 6, doc.valor_liquido, moeda)
                worksheet.write(row, 7, status_texto)
                row += 1

            # Ajustar largura das colunas
            worksheet.set_column(0, 0, 15)
            worksheet.set_column(1, 1, 30)
            worksheet.set_column(2, 2, 15)
            worksheet.set_column(3, 6, 15)
            worksheet.set_column(7, 7, 10)

            # Planilha de resumo
            resumo_sheet.write(0, 0, "Resumo Financeiro", titulo)
            resumo_sheet.write(
                1, 0, f"Período: {context['data_inicio']} a {context['data_fim']}"
            )

            resumo_sheet.write(3, 0, "Métrica", cabecalho)
            resumo_sheet.write(3, 1, "Valor", cabecalho)

            resumo_sheet.write(4, 0, "Total Bruto")
            resumo_sheet.write(4, 1, resumo["total_bruto"], moeda)

            resumo_sheet.write(5, 0, "Total ISS")
            resumo_sheet.write(5, 1, resumo["total_iss"], moeda)

            resumo_sheet.write(6, 0, "Total IRRF")
            resumo_sheet.write(6, 1, resumo["total_irrf"], moeda)

            resumo_sheet.write(7, 0, "Total Líquido")
            resumo_sheet.write(7, 1, resumo["total_liquido"], moeda)

            resumo_sheet.write(9, 0, "Quantidade de Documentos")
            resumo_sheet.write(9, 1, resumo["quantidade"])

            resumo_sheet.write(10, 0, "Pendentes")
            resumo_sheet.write(10, 1, resumo["pendentes"])

            resumo_sheet.write(11, 0, "Pagos")
            resumo_sheet.write(11, 1, resumo["pagos"])

            resumo_sheet.write(12, 0, "Atrasados")
            resumo_sheet.write(12, 1, resumo["atrasados"])

            # Ajustar largura das colunas
            resumo_sheet.set_column(0, 0, 25)
            resumo_sheet.set_column(1, 1, 15)

            workbook.close()

            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                'attachment; filename="relatorio_financeiro.xlsx"'
            )
            return response

        return context
