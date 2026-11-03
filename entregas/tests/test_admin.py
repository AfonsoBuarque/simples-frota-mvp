"""Testes de integração: admin do Django, ORM e banco de dados trabalhando juntos."""

from django.test import TestCase
from django.urls import reverse

from entregas.models import Comprovante, Entrega, Usuario


class AdminIntegracaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_superuser(
            "admin", "admin@example.com", "senha-forte-123"
        )
        cls.motorista = Usuario.objects.create_user("motorista1", password="x")
        cls.entrega = Entrega.objects.create(
            cliente="Mercado Central", endereco="Rua A, 100", motorista=cls.motorista
        )
        Comprovante.objects.create(entrega=cls.entrega)

    def setUp(self):
        self.client.force_login(self.admin)

    def test_admin_exige_login(self):
        self.client.logout()
        resposta = self.client.get(reverse("admin:entregas_entrega_changelist"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/admin/login/", resposta["Location"])

    def test_lista_de_entregas_mostra_cliente_e_motorista(self):
        resposta = self.client.get(reverse("admin:entregas_entrega_changelist"))
        self.assertContains(resposta, "Mercado Central")
        self.assertContains(resposta, "motorista1")

    def test_busca_de_entregas_filtra_por_cliente(self):
        Entrega.objects.create(cliente="Padaria Sol", endereco="Rua C, 9")
        url = reverse("admin:entregas_entrega_changelist")
        resposta = self.client.get(url, {"q": "Padaria"})
        self.assertContains(resposta, "Padaria Sol")
        self.assertNotContains(resposta, "Mercado Central")

    def test_cadastro_de_entrega_pelo_admin_grava_no_banco(self):
        resposta = self.client.post(
            reverse("admin:entregas_entrega_add"),
            {
                "cliente": "Loja Nova",
                "endereco": "Av. Principal, 1",
                "observacoes": "",
                "status": Entrega.Status.PENDENTE,
                "motorista": self.motorista.pk,
            },
        )
        self.assertEqual(resposta.status_code, 302)
        nova = Entrega.objects.get(cliente="Loja Nova")
        self.assertEqual(nova.motorista, self.motorista)

    def test_admin_nao_aceita_gerente_como_motorista_da_entrega(self):
        gerente = Usuario.objects.create_user(
            "gerente1", password="x", perfil=Usuario.Perfil.GERENTE
        )
        resposta = self.client.post(
            reverse("admin:entregas_entrega_add"),
            {
                "cliente": "Loja Y",
                "endereco": "Rua Z, 2",
                "status": Entrega.Status.PENDENTE,
                "motorista": gerente.pk,
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Entrega.objects.filter(cliente="Loja Y").exists())

    def test_lista_de_usuarios_e_comprovantes_carregam(self):
        for nome in ("entregas_usuario_changelist", "entregas_comprovante_changelist"):
            resposta = self.client.get(reverse(f"admin:{nome}"))
            self.assertEqual(resposta.status_code, 200)
