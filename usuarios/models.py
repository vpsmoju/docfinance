from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Perfil(models.Model):
    """
    Modelo para armazenar informações adicionais do usuário.
    Cada perfil está vinculado a um usuário do Django e contém informações como
    telefone, foto, matrícula, CPF e status da conta.
    """

    STATUS_CHOICES = (
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("rejeitado", "Rejeitado"),
    )

    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil"
    )
    telefone = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to="fotos_perfil/", blank=True, null=True)
    matricula = models.CharField(max_length=20, blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pendente")
    token_ativacao = models.CharField(max_length=100, blank=True, null=True)
    data_token = models.DateTimeField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"  # pylint: disable=no-member


class LogAtividade(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    acao = models.CharField(max_length=100)
    detalhes = models.TextField()
    data_hora = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(
        null=True, blank=True
    )  # Adicionando o campo ip novamente

    class Meta:
        ordering = ["-data_hora"]
        verbose_name = "Log de Atividade"
        verbose_name_plural = "Logs de Atividades"

    def __str__(self):
        return f"{self.usuario.username} - {self.acao} - {self.data_hora}"  # pylint: disable=no-member


@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    if created:
        Perfil.objects.create(usuario=instance)  # pylint: disable=no-member


@receiver(post_save, sender=User)
def salvar_perfil(sender, instance, **kwargs):  # pylint: disable=unused-argument
    # Verificar se o perfil existe antes de tentar salvá-lo
    try:
        instance.perfil.save()
    except User.perfil.RelatedObjectDoesNotExist:  # pylint: disable=no-member
        # Se o perfil não existir, crie um novo
        Perfil.objects.create(usuario=instance)  # pylint: disable=no-member
