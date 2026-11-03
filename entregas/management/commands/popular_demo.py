import base64
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from entregas.models import Comprovante, Entrega, Usuario

SENHA_DEMO = "demo12345"

# PNG transparente de 1x1 pixel, usado como assinatura de exemplo.
PNG_1X1 = base64.b64encode(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
        "1f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082"
    )
).decode()


class Command(BaseCommand):
    help = "Cria usuários e entregas de exemplo para desenvolvimento local."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Apaga as entregas antes de recriar."
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Este comando só roda com DJANGO_DEBUG=True.")

        if options["reset"]:
            Entrega.objects.all().delete()

        gerente = self._usuario("gerente", "Afonso", "Pena", Usuario.Perfil.GERENTE)
        carlos = self._usuario("carlos", "Carlos", "Souza", Usuario.Perfil.MOTORISTA)
        marina = self._usuario("marina", "Marina", "Lima", Usuario.Perfil.MOTORISTA)

        if Entrega.objects.exists():
            self.stdout.write("Entregas já existem; use --reset para recriar.")
        else:
            agora = timezone.now()
            dados = [
                ("Mercado Bom Preço", "Rua das Flores, 120 - Vila Progresso", carlos, Entrega.Status.PENDENTE, agora + timedelta(hours=3), "Entregar na doca dos fundos."),
                ("Padaria Sol Nascente", "Av. Central, 45 - Vila Progresso", carlos, Entrega.Status.EM_ROTA, agora + timedelta(hours=1), ""),
                ("Farmácia Saúde", "Rua do Comércio, 300 - Centro", carlos, Entrega.Status.PENDENTE, agora - timedelta(hours=2), "Cliente aguardando, prioridade."),
                ("Loja Casa Nova", "Rua Verde, 18 - Jardim Alegre", marina, Entrega.Status.PENDENTE, agora + timedelta(hours=5), ""),
                ("Restaurante Sabor Caseiro", "Av. das Palmeiras, 900", marina, Entrega.Status.EM_ROTA, agora - timedelta(minutes=30), "Tocar a campainha dos fundos."),
                ("Escola Pequeno Passo", "Rua da Escola, 7", carlos, Entrega.Status.ENTREGUE, agora - timedelta(hours=4), ""),
            ]
            for cliente, endereco, motorista, status, prazo, obs in dados:
                entrega = Entrega.objects.create(
                    cliente=cliente, endereco=endereco, motorista=motorista,
                    status=status, prazo=prazo, observacoes=obs,
                )
                if status == Entrega.Status.ENTREGUE:
                    Comprovante.objects.create(
                        entrega=entrega, assinatura=f"data:image/png;base64,{PNG_1X1}"
                    )
            self.stdout.write(self.style.SUCCESS("Entregas de exemplo criadas."))

        self.stdout.write(
            f"Usuários de exemplo (senha {SENHA_DEMO}): "
            f"{gerente.username}, {carlos.username}, {marina.username}"
        )

    def _usuario(self, username, nome, sobrenome, perfil):
        usuario, criado = Usuario.objects.get_or_create(
            username=username,
            defaults={"first_name": nome, "last_name": sobrenome, "perfil": perfil},
        )
        if criado:
            usuario.set_password(SENHA_DEMO)
            usuario.save()
        return usuario
