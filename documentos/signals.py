from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from usuarios.models import LogAtividade
from usuarios.middleware import thread_local

from .models import Documento, Recurso


def _get_actor_and_ip():
    user = getattr(thread_local, "current_user", None)
    ip = getattr(thread_local, "current_ip", None)
    return user, ip


@receiver(post_save, sender=Documento)
def log_documento_save(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    usuario, ip = _get_actor_and_ip()
    acao = "Criação de Documento" if created else "Atualização de Documento"
    detalhes = (
        f"Documento {instance.numero} ({instance.tipo}) do fornecedor {instance.fornecedor.nome}"
    )
    LogAtividade.objects.create(  # pylint: disable=no-member
        usuario=usuario,
        acao=acao,
        detalhes=detalhes,
        ip=ip,
    )


@receiver(post_delete, sender=Documento)
def log_documento_delete(sender, instance, **kwargs):  # pylint: disable=unused-argument
    usuario, ip = _get_actor_and_ip()
    acao = "Exclusão de Documento"
    detalhes = (
        f"Documento {instance.numero} do fornecedor {getattr(instance.fornecedor, 'nome', '-') } foi excluído"
    )
    LogAtividade.objects.create(  # pylint: disable=no-member
        usuario=usuario,
        acao=acao,
        detalhes=detalhes,
        ip=ip,
    )


@receiver(post_save, sender=Recurso)
def log_recurso_save(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    usuario, ip = _get_actor_and_ip()
    acao = "Criação de Recurso" if created else "Atualização de Recurso"
    detalhes = f"Recurso {instance.codigo} - {instance.nome} (Secretaria: {instance.secretaria.codigo})"
    LogAtividade.objects.create(  # pylint: disable=no-member
        usuario=usuario,
        acao=acao,
        detalhes=detalhes,
        ip=ip,
    )


@receiver(post_delete, sender=Recurso)
def log_recurso_delete(sender, instance, **kwargs):  # pylint: disable=unused-argument
    usuario, ip = _get_actor_and_ip()
    acao = "Exclusão de Recurso"
    detalhes = f"Recurso {instance.codigo} - {instance.nome} foi excluído"
    LogAtividade.objects.create(  # pylint: disable=no-member
        usuario=usuario,
        acao=acao,
        detalhes=detalhes,
        ip=ip,
    )

