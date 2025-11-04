"""Configuração de URLs para o módulo de relatórios.

Este módulo define os padrões de URL para a funcionalidade de relatórios,
incluindo visualizações para diferentes tipos de relatórios e opções de
exportação de dados.
"""

from django.urls import path

from . import views

app_name = "relatorios"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("fornecedores/", views.relatorio_fornecedores, name="fornecedores"),
    path("secretaria/", views.relatorio_secretaria, name="secretaria"),
    path("recurso/", views.relatorio_recurso, name="recurso"),
    path("financeiro/", views.relatorio_financeiro, name="financeiro"),
    path("exportar/csv/", views.exportar_csv, name="exportar_csv"),
    path("exportar/excel/", views.exportar_excel, name="exportar_excel"),
    path("dados-grafico/", views.dados_grafico, name="dados_grafico"),
    path(
        "filtro-encaminhamento/",
        views.filtro_encaminhamento,
        name="filtro_encaminhamento",
    ),
    path(
        "encaminhamento/",
        views.relatorio_encaminhamento,
        name="relatorio_encaminhamento",
    ),
    path(
        "contabilidade/", views.relatorio_contabilidade, name="relatorio_contabilidade"
    ),
    path("pagamentos/", views.relatorio_pagamentos, name="pagamentos"),
]
