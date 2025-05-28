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
    path("dashboard/", views.dashboard, name="dashboard"),
]
