from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from entregas.forms import EntregaForm
from entregas.models import Comprovante, Entrega, Usuario


class BaseGerenteTest(TestCase):
    def setUp(self):
        self.gerente = Usuario.objects.create_user(
            "gerente", password="x12345678", perfil=Usuario.Perfil.GERENTE
        )
        self.carlos = Usuario.objects.create_user(
            "carlos", password="x12345678", perfil=Usuario.Perfil.MOTORISTA,
            first_name="Carlos", last_name="Souza",
        )
        self.client.force_login(self.gerente)


class PainelTests(BaseGerenteTest):
    def setUp(self):
        super().setUp()
        agora = timezone.now()
        self.pendente = Entrega.objects.create(cliente="Mercado", endereco="A", motorista=self.carlos)
        self.atrasada = Entrega.objects.create(
            cliente="Farmácia", endereco="B", motorista=self.carlos,
            status=Entrega.Status.EM_ROTA, prazo=agora - timedelta(hours=1),
        )
        self.entregue = Entrega.objects.create(
            cliente="Escola", endereco="C", status=Entrega.Status.ENTREGUE,
            prazo=agora - timedelta(hours=2),
        )
        Comprovante.objects.create(entrega=self.entregue, assinatura="data:image/png;base64,AA")

    def test_inicio_leva_gerente_ao_painel(self):
        self.assertRedirects(self.client.get(reverse("entregas:inicio")), reverse("entregas:painel"))

    def test_contagens(self):
        r = self.client.get(reverse("entregas:painel"))
        c = r.context["contagem"]
        self.assertEqual((c["total"], c["pendentes"], c["em_rota"], c["entregues"], c["atrasadas"]), (3, 1, 1, 1, 1))

    def test_entregue_fora_do_prazo_nao_conta_como_atrasada(self):
        r = self.client.get(reverse("entregas:painel") + "?status=atrasadas")
        self.assertEqual(list(r.context["entregas"]), [self.atrasada])

    def test_filtro_por_status(self):
        r = self.client.get(reverse("entregas:painel") + "?status=pendente")
        self.assertEqual(list(r.context["entregas"]), [self.pendente])

    def test_filtro_invalido_mostra_todas(self):
        r = self.client.get(reverse("entregas:painel") + "?status=xpto")
        self.assertEqual(r.context["filtro"], "todas")
        self.assertEqual(len(r.context["entregas"]), 3)

    def test_mostra_atraso_motorista_e_comprovante(self):
        r = self.client.get(reverse("entregas:painel"))
        self.assertContains(r, "Atrasada")
        self.assertContains(r, "Carlos Souza")
        self.assertContains(r, "Sem motorista")
        self.assertContains(r, 'aria-current="page"')

    def test_filtro_vazio(self):
        Entrega.objects.all().delete()
        self.assertContains(self.client.get(reverse("entregas:painel")), "Nenhuma entrega neste filtro.")

    def test_consultas_nao_crescem_com_entregas(self):
        for i in range(10):
            Entrega.objects.create(cliente=f"C{i}", endereco="X", motorista=self.carlos)
        with self.assertNumQueries(4):  # sessão, usuário, contagem, lista
            self.client.get(reverse("entregas:painel"))

    def test_motorista_nao_acessa_painel(self):
        self.client.force_login(self.carlos)
        self.assertEqual(self.client.get(reverse("entregas:painel")).status_code, 403)
        self.assertEqual(self.client.get(reverse("entregas:nova_entrega")).status_code, 403)


class NovaEntregaTests(BaseGerenteTest):
    def test_formulario_renderiza(self):
        r = self.client.get(reverse("entregas:nova_entrega"))
        self.assertContains(r, 'type="datetime-local"')
        self.assertContains(r, 'aria-describedby="id_prazo_ajuda"')

    def test_cadastra_entrega(self):
        r = self.client.post(reverse("entregas:nova_entrega"), {
            "cliente": "Padaria", "endereco": "Rua 1", "observacoes": "",
            "prazo": "2030-01-10T14:30", "motorista": self.carlos.pk,
        })
        self.assertRedirects(r, reverse("entregas:painel"))
        entrega = Entrega.objects.get(cliente="Padaria")
        self.assertEqual(entrega.motorista, self.carlos)
        self.assertEqual(entrega.status, Entrega.Status.PENDENTE)

    def test_campos_obrigatorios(self):
        r = self.client.post(reverse("entregas:nova_entrega"), {})
        self.assertContains(r, "Confira os campos destacados abaixo.")
        self.assertFalse(Entrega.objects.exists())


class EntregaFormTests(BaseGerenteTest):
    def test_lista_apenas_motoristas_ativos(self):
        inativo = Usuario.objects.create_user("ze", perfil=Usuario.Perfil.MOTORISTA, is_active=False)
        opcoes = list(EntregaForm().fields["motorista"].queryset)
        self.assertEqual(opcoes, [self.carlos])
        self.assertNotIn(inativo, opcoes)
        self.assertNotIn(self.gerente, opcoes)

    def test_rejeita_gerente_como_motorista(self):
        form = EntregaForm(data={"cliente": "X", "endereco": "Y", "motorista": self.gerente.pk})
        self.assertFalse(form.is_valid())
        self.assertIn("motorista", form.errors)

    def test_rotulo_do_motorista_usa_nome(self):
        self.assertEqual(EntregaForm().fields["motorista"].label_from_instance(self.carlos), "Carlos Souza")
