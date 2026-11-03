import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    """Usuário do sistema: gerente ou motorista da Simples Frota."""

    class Perfil(models.TextChoices):
        GERENTE = "gerente", "Gerente"
        MOTORISTA = "motorista", "Motorista"

    perfil = models.CharField(
        max_length=10, choices=Perfil.choices, default=Perfil.MOTORISTA
    )

    @property
    def eh_gerente(self):
        return self.perfil == self.Perfil.GERENTE

    @property
    def eh_motorista(self):
        return self.perfil == self.Perfil.MOTORISTA


class Entrega(models.Model):
    """Entrega cadastrada pelo gerente e atribuída a um motorista."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_ROTA = "em_rota", "Em rota"
        ENTREGUE = "entregue", "Entregue"
        OCORRENCIA = "ocorrencia", "Ocorrência"

    class MotivoOcorrencia(models.TextChoices):
        CLIENTE_AUSENTE = "cliente_ausente", "Cliente ausente"
        ENDERECO_ERRADO = "endereco_errado", "Endereço errado ou não encontrado"
        RECUSADA = "recusada", "Cliente recusou a entrega"
        OUTRO = "outro", "Outro motivo"

    #: Status em que a entrega ainda está em andamento.
    STATUS_ABERTOS = (Status.PENDENTE, Status.EM_ROTA)

    cliente = models.CharField(max_length=120)
    endereco = models.CharField(max_length=255)
    observacoes = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDENTE
    )
    prazo = models.DateTimeField(
        null=True, blank=True, help_text="Data e hora limite para a entrega."
    )
    motorista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entregas",
        limit_choices_to={"perfil": "motorista"},
    )
    motivo_ocorrencia = models.CharField(
        max_length=20, choices=MotivoOcorrencia.choices, blank=True
    )
    detalhe_ocorrencia = models.CharField(
        max_length=300, blank=True, help_text="Explicação do motorista."
    )
    ocorrencia_em = models.DateTimeField(null=True, blank=True)
    token_consulta = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Identificador do link público de consulta de status.",
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criada_em"]
        verbose_name = "entrega"
        verbose_name_plural = "entregas"

    def __str__(self):
        return f"Entrega #{self.pk} - {self.cliente}"

    @property
    def atrasada(self):
        """Atrasada: passou do prazo e ainda está em andamento.

        Entregas concluídas ou com ocorrência registrada já têm um desfecho
        e são tratadas à parte no painel.
        """
        return (
            self.prazo is not None
            and self.status in self.STATUS_ABERTOS
            and self.prazo < timezone.now()
        )

    def registrar_ocorrencia(self, motivo, detalhe=""):
        """Encerra a tentativa de entrega com o motivo informado pelo motorista."""
        self.status = self.Status.OCORRENCIA
        self.motivo_ocorrencia = motivo
        self.detalhe_ocorrencia = detalhe
        self.ocorrencia_em = timezone.now()
        self.save(
            update_fields=[
                "status", "motivo_ocorrencia", "detalhe_ocorrencia",
                "ocorrencia_em", "atualizada_em",
            ]
        )


class Comprovante(models.Model):
    """Comprovante digital (foto ou assinatura) de uma entrega."""

    entrega = models.OneToOneField(
        Entrega, on_delete=models.CASCADE, related_name="comprovante"
    )
    foto = models.ImageField(upload_to="comprovantes/%Y/%m/", blank=True)
    assinatura = models.TextField(
        blank=True, help_text="Assinatura desenhada na tela (imagem em base64)."
    )
    registrado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "comprovante"
        verbose_name_plural = "comprovantes"

    def __str__(self):
        return f"Comprovante da entrega #{self.entrega_id}"
