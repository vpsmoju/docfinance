from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from usuarios.models import LogAtividade
from usuarios.middleware import thread_local

from .models import Fornecedor


def _get_actor_and_ip():
    user = getattr(thread_local, "current_user", None)
    ip = getattr(thread_local, "current_ip", None)
    return user, ip


@receiver(post_save, sender=Fornecedor)
def log_fornecedor_save(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    usuario, ip = _get_actor_and_ip()
    acao = "Criação de Fornecedor" if created else "Atualização de Fornecedor"
    detalhes = f"Fornecedor {instance.nome} ({instance.cnpj_cpf})"
    LogAtividade.objects.create(  # pylint: disable=no-member
        usuario=usuario,
        acao=acao,
        detalhes=detalhes,
        ip=ip,
    )


@receiver(post_delete, sender=Fornecedor)
def log_fornecedor_delete(sender, instance, **kwargs):  # pylint: disable=unused-argument
    usuario, ip = _get_actor_and_ip()
    acao = "Exclusão de Fornecedor"
    detalhes = f"Fornecedor {instance.nome} ({instance.cnpj_cpf}) foi excluído"
    LogAtividade.objects.create(  # pylint: disable=no-member
        usuario=usuario,
        acao=acao,
        detalhes=detalhes,
        ip=ip,
    )

