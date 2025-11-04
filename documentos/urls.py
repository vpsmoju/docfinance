from django.urls import path

from . import api, views

app_name = "documentos"

urlpatterns = [
    path("", views.DocumentoListView.as_view(), name="list"),
    path("novo/", views.DocumentoCreateView.as_view(), name="create"),
    path("<int:pk>/", views.DocumentoDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.DocumentoUpdateView.as_view(), name="update"),
    path("<int:pk>/excluir/", views.DocumentoDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/dar-baixa/", views.DarBaixaDocumentoView.as_view(), name="dar_baixa"
    ),
    path(
        "api/buscar-fornecedor/",
        api.buscar_fornecedor_por_cnpj_cpf,
        name="buscar_fornecedor",
    ),
    path(
        "api/recursos-por-secretaria/<int:secretaria_id>/",
        api.recursos_por_secretaria,
        name="recursos_por_secretaria",
    ),
    # Gestão de Secretarias/Recursos
    path("recursos/", views.gestao_recursos, name="gestao_recursos"),
    path(
        "recursos/secretaria/<int:pk>/editar/",
        views.editar_secretaria,
        name="editar_secretaria",
    ),
    path(
        "recursos/secretaria/<int:pk>/excluir/",
        views.excluir_secretaria,
        name="excluir_secretaria",
    ),
    path(
        "recursos/recurso/<int:pk>/editar/",
        views.editar_recurso,
        name="editar_recurso",
    ),
    path(
        "recursos/recurso/<int:pk>/excluir/",
        views.excluir_recurso,
        name="excluir_recurso",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
]
