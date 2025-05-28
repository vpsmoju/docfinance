from django.urls import path

from . import views

app_name = "fornecedores"

urlpatterns = [
    path("", views.FornecedorListView.as_view(), name="fornecedor_list"),
    path("<int:pk>/", views.FornecedorDetailView.as_view(), name="fornecedor_detail"),
    path("novo/", views.FornecedorCreateView.as_view(), name="fornecedor_create"),
    path(
        "<int:pk>/editar/",
        views.FornecedorUpdateView.as_view(),
        name="fornecedor_update",
    ),
    path(
        "<int:pk>/excluir/",
        views.FornecedorDeleteView.as_view(),
        name="fornecedor_delete",
    ),
]
