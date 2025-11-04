from django.http import JsonResponse

from .models import Fornecedor, Recurso


def buscar_fornecedor_por_cnpj_cpf(request):
    """
    Pesquisar um fornecedor (fornecedor) pelo número do CPF ou CNPJ.

    Args:
        solicitação: objeto de solicitação HTTP contendo o parâmetro 'cnpj_cpf' em GET

    Returns:
        JsonResponse: Contém detalhes do fornecedor (id, nome, cpf/cnpj) se encontrado,
                     ou mensagem de erro se não for encontrado ou se cpf/cnpj não for fornecido
    """
    cnpj_cpf = request.GET.get("cnpj_cpf")
    if not cnpj_cpf:
        return JsonResponse({"error": "CPF/CNPJ não fornecido"})

    # Remove caracteres não numéricos
    cnpj_cpf = "".join(filter(str.isdigit, cnpj_cpf))

    try:
        fornecedor = Fornecedor.objects.get(cnpj_cpf=cnpj_cpf)
        return JsonResponse(
            {
                "id": fornecedor.id,
                "nome": fornecedor.nome,
                "cnpj_cpf": fornecedor.cnpj_cpf,
            }
        )
    except Fornecedor.DoesNotExist:
        return JsonResponse({"error": "Fornecedor não encontrado"})


def recursos_por_secretaria(request, secretaria_id):
    """Retorna recursos (id, nome) de uma secretaria específica em JSON."""
    recursos = (
        Recurso.objects.filter(secretaria_id=secretaria_id)
        .order_by("nome")
        .values("id", "nome")
    )
    return JsonResponse({"recursos": list(recursos)})
