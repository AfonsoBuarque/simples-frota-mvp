import uuid
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from entregas.models import Comprovante, Entrega, Usuario


class AcompanharTests(TestCase):
    def setUp(self):
        self.motorista = Usuario.objects.create_user(
            "carlos", perfil=Usuario.Perfil.MOTORISTA, first_name="Carlos", last_name="Souza"
        )
        self.entrega = Entrega.objects.create(
            cliente="Mercado Bom Preço", endereco="Rua Secreta, 99",
            observacoes="Portão azul", motorista=self.motorista,
            prazo=timezone.now() + timedelta(hours=2),
        )
        self.url = reverse("entregas:acompanhar", args=[self.entrega.token_consulta])

    def test_acesso_sem_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Mercado Bom Preço")
        self.assertContains(r, "Pedido registrado")
        self.assertContains(r, 'aria-current="step"')

    def test_nao_expoe_dados_internos(self):
        r = self.client.get(self.url)
        for dado in ("Rua Secreta", "Portão azul", "Carlos"):
            self.assertNotContains(r, dado)

    def test_nao_indexa_e_nao_guarda_cache(self):
        r = self.client.get(self.url)
        self.assertEqual(r["X-Robots-Tag"], "noindex, nofollow")
        self.assertIn("no-cache", r["Cache-Control"])
        self.assertContains(r, '<meta name="robots" content="noindex, nofollow">')

    def test_token_inexistente_404(self):
        r = self.client.get(reverse("entregas:acompanhar", args=[uuid.uuid4()]))
        self.assertEqual(r.status_code, 404)

    def test_id_numerico_nao_funciona(self):
        self.assertEqual(self.client.get(f"/acompanhar/{self.entrega.pk}/").status_code, 404)

    def test_post_nao_permitido(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_em_rota_marca_etapas(self):
        self.entrega.status = Entrega.Status.EM_ROTA
        self.entrega.save()
        etapas = self.client.get(self.url).context["etapas"]
        self.assertEqual([(e["concluida"], e["atual"]) for e in etapas], [(True, False), (False, True), (False, False)])

    def test_atrasada_mostra_aviso(self):
        self.entrega.prazo = timezone.now() - timedelta(hours=1)
        self.entrega.save()
        self.assertContains(self.client.get(self.url), "passou do prazo previsto")

    def test_entregue_mostra_horario_do_comprovante(self):
        self.entrega.status = Entrega.Status.ENTREGUE
        self.entrega.save()
        Comprovante.objects.create(entrega=self.entrega, assinatura="data:image/png;base64,AA")
        r = self.client.get(self.url)
        self.assertContains(r, "com comprovante registrado")
        self.assertNotContains(r, "Previsão:")

    def test_painel_tem_link_do_cliente(self):
        gerente = Usuario.objects.create_user("g", perfil=Usuario.Perfil.GERENTE)
        self.client.force_login(gerente)
        self.assertContains(self.client.get(reverse("entregas:painel")), self.url)
