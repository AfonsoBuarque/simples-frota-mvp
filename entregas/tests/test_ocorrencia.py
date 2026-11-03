from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from entregas.forms import OcorrenciaForm
from entregas.models import Entrega, Usuario


class OcorrenciaModeloTests(TestCase):
    def test_registrar_ocorrencia_grava_motivo_e_horario(self):
        entrega = Entrega.objects.create(cliente="X", endereco="Y", status=Entrega.Status.EM_ROTA)
        entrega.registrar_ocorrencia(Entrega.MotivoOcorrencia.CLIENTE_AUSENTE, "Portão fechado")
        entrega.refresh_from_db()
        self.assertEqual(entrega.status, Entrega.Status.OCORRENCIA)
        self.assertEqual(entrega.motivo_ocorrencia, "cliente_ausente")
        self.assertEqual(entrega.detalhe_ocorrencia, "Portão fechado")
        self.assertIsNotNone(entrega.ocorrencia_em)

    def test_ocorrencia_vencida_nao_conta_como_atrasada(self):
        entrega = Entrega.objects.create(
            cliente="X", endereco="Y", status=Entrega.Status.OCORRENCIA,
            prazo=timezone.now() - timedelta(hours=1),
        )
        self.assertFalse(entrega.atrasada)


class OcorrenciaFormTests(TestCase):
    def test_motivo_obrigatorio(self):
        form = OcorrenciaForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("Escolha o motivo da ocorrência.", form.errors["motivo"])

    def test_outro_exige_detalhe(self):
        form = OcorrenciaForm(data={"motivo": "outro", "detalhe": "  "})
        self.assertFalse(form.is_valid())
        self.assertIn("Descreva o motivo da ocorrência.", form.errors["detalhe"])

    def test_motivo_fora_da_lista_recusado(self):
        self.assertFalse(OcorrenciaForm(data={"motivo": "inventado"}).is_valid())

    def test_detalhe_com_html_recusado(self):
        form = OcorrenciaForm(data={"motivo": "recusada", "detalhe": "<script>alert(1)</script>"})
        self.assertFalse(form.is_valid())

    def test_detalhe_limitado_a_300(self):
        self.assertFalse(OcorrenciaForm(data={"motivo": "outro", "detalhe": "a" * 301}).is_valid())


class OcorrenciaViewTests(TestCase):
    def setUp(self):
        self.carlos = Usuario.objects.create_user("carlos", perfil=Usuario.Perfil.MOTORISTA)
        self.marina = Usuario.objects.create_user("marina", perfil=Usuario.Perfil.MOTORISTA)
        self.gerente = Usuario.objects.create_user("g", perfil=Usuario.Perfil.GERENTE)
        self.entrega = Entrega.objects.create(
            cliente="Casa de Ração Pet", endereco="Rua A", motorista=self.carlos,
            status=Entrega.Status.EM_ROTA,
        )
        self.url = reverse("entregas:registrar_ocorrencia", args=[self.entrega.pk])
        self.client.force_login(self.carlos)

    def test_lista_mostra_botao_para_entrega_em_rota(self):
        r = self.client.get(reverse("entregas:minhas_entregas"))
        self.assertContains(r, "Não consegui entregar")
        self.assertContains(r, self.url)

    def test_tela_de_comprovante_oferece_alternativa(self):
        r = self.client.get(reverse("entregas:registrar_comprovante", args=[self.entrega.pk]))
        self.assertContains(r, self.url)

    def test_formulario_acessivel(self):
        r = self.client.get(self.url)
        self.assertContains(r, "<legend")
        self.assertContains(r, 'type="radio"', count=4)

    def test_registra_ocorrencia(self):
        r = self.client.post(self.url, {"motivo": "cliente_ausente", "detalhe": "Loja fechada"}, follow=True)
        self.assertRedirects(r, reverse("entregas:minhas_entregas"))
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.OCORRENCIA)
        self.assertContains(r, "Ocorrência registrada para Casa de Ração Pet")
        self.assertContains(r, "Encerradas recentemente")

    def test_sem_motivo_mostra_erro_e_nao_altera(self):
        r = self.client.post(self.url, {})
        self.assertContains(r, "Escolha o motivo da ocorrência.")
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.EM_ROTA)

    def test_pendente_nao_aceita_ocorrencia(self):
        self.entrega.status = Entrega.Status.PENDENTE
        self.entrega.save()
        self.assertRedirects(self.client.post(self.url, {"motivo": "recusada"}), reverse("entregas:minhas_entregas"))
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.PENDENTE)

    def test_entregue_nao_aceita_ocorrencia(self):
        self.entrega.status = Entrega.Status.ENTREGUE
        self.entrega.save()
        self.client.post(self.url, {"motivo": "recusada"})
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.ENTREGUE)

    def test_ocorrencia_impede_comprovante(self):
        self.entrega.registrar_ocorrencia("recusada")
        r = self.client.get(reverse("entregas:registrar_comprovante", args=[self.entrega.pk]))
        self.assertRedirects(r, reverse("entregas:minhas_entregas"))

    def test_outro_motorista_404(self):
        self.client.force_login(self.marina)
        self.assertEqual(self.client.post(self.url, {"motivo": "recusada"}).status_code, 404)

    def test_gerente_403(self):
        self.client.force_login(self.gerente)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_painel_mostra_ocorrencia_e_motivo(self):
        self.entrega.registrar_ocorrencia("endereco_errado", "Número não existe")
        self.client.force_login(self.gerente)
        r = self.client.get(reverse("entregas:painel"))
        self.assertEqual(r.context["contagem"]["ocorrencias"], 1)
        self.assertContains(r, "Endereço errado ou não encontrado: Número não existe")
        filtrado = self.client.get(reverse("entregas:painel") + "?status=ocorrencia")
        self.assertEqual(list(filtrado.context["entregas"]), [self.entrega])

    def test_pagina_publica_sem_expor_detalhe(self):
        self.entrega.registrar_ocorrencia("cliente_ausente", "Vizinho disse que viajou")
        self.client.logout()
        r = self.client.get(reverse("entregas:acompanhar", args=[self.entrega.token_consulta]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Não foi possível concluir a entrega")
        self.assertNotContains(r, "Vizinho disse que viajou")
        self.assertEqual(len(r.context["etapas"]), 2)
