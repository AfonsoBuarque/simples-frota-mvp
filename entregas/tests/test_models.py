from datetime import timedelta

from django.contrib.auth.hashers import identify_hasher
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from entregas.models import Comprovante, Entrega, Usuario


class UsuarioTests(TestCase):
    def test_perfil_padrao_eh_motorista(self):
        usuario = Usuario.objects.create_user("joao", password="senha-forte-123")
        self.assertEqual(usuario.perfil, Usuario.Perfil.MOTORISTA)
        self.assertTrue(usuario.eh_motorista)
        self.assertFalse(usuario.eh_gerente)

    def test_perfil_gerente(self):
        usuario = Usuario.objects.create_user(
            "afonso", password="senha-forte-123", perfil=Usuario.Perfil.GERENTE
        )
        self.assertTrue(usuario.eh_gerente)
        self.assertFalse(usuario.eh_motorista)

    def test_senha_eh_gravada_com_argon2(self):
        usuario = Usuario.objects.create_user("maria", password="senha-forte-123")
        self.assertEqual(identify_hasher(usuario.password).algorithm, "argon2")
        self.assertTrue(usuario.check_password("senha-forte-123"))


class EntregaTests(TestCase):
    def setUp(self):
        self.motorista = Usuario.objects.create_user("motorista1", password="x")

    def criar_entrega(self, **extra):
        dados = {"cliente": "Mercado Central", "endereco": "Rua A, 100"}
        dados.update(extra)
        return Entrega.objects.create(**dados)

    def test_status_inicial_eh_pendente(self):
        self.assertEqual(self.criar_entrega().status, Entrega.Status.PENDENTE)

    def test_token_de_consulta_eh_unico_e_gerado_automaticamente(self):
        a, b = self.criar_entrega(), self.criar_entrega()
        self.assertIsNotNone(a.token_consulta)
        self.assertNotEqual(a.token_consulta, b.token_consulta)

    def test_str_identifica_a_entrega(self):
        entrega = self.criar_entrega()
        self.assertEqual(str(entrega), f"Entrega #{entrega.pk} - Mercado Central")

    def test_sem_prazo_nao_esta_atrasada(self):
        self.assertFalse(self.criar_entrega().atrasada)

    def test_prazo_vencido_e_nao_entregue_esta_atrasada(self):
        entrega = self.criar_entrega(prazo=timezone.now() - timedelta(hours=1))
        self.assertTrue(entrega.atrasada)

    def test_prazo_no_futuro_nao_esta_atrasada(self):
        entrega = self.criar_entrega(prazo=timezone.now() + timedelta(hours=1))
        self.assertFalse(entrega.atrasada)

    def test_entrega_concluida_nao_conta_como_atrasada(self):
        entrega = self.criar_entrega(
            prazo=timezone.now() - timedelta(hours=1),
            status=Entrega.Status.ENTREGUE,
        )
        self.assertFalse(entrega.atrasada)

    def test_remover_motorista_mantem_a_entrega_sem_responsavel(self):
        entrega = self.criar_entrega(motorista=self.motorista)
        self.motorista.delete()
        entrega.refresh_from_db()
        self.assertIsNone(entrega.motorista)

    def test_entregas_sao_listadas_da_mais_recente_para_a_mais_antiga(self):
        primeira, segunda = self.criar_entrega(), self.criar_entrega()
        self.assertEqual(list(Entrega.objects.all()), [segunda, primeira])


class ComprovanteTests(TestCase):
    def setUp(self):
        self.entrega = Entrega.objects.create(cliente="Padaria", endereco="Rua B, 5")

    def test_comprovante_se_liga_a_entrega(self):
        comprovante = Comprovante.objects.create(
            entrega=self.entrega, assinatura="data:image/png;base64,AAAA"
        )
        self.assertEqual(self.entrega.comprovante, comprovante)
        self.assertIsNotNone(comprovante.registrado_em)
        self.assertEqual(
            str(comprovante), f"Comprovante da entrega #{self.entrega.pk}"
        )

    def test_cada_entrega_aceita_apenas_um_comprovante(self):
        Comprovante.objects.create(entrega=self.entrega)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Comprovante.objects.create(entrega=self.entrega)

    def test_remover_a_entrega_remove_o_comprovante(self):
        Comprovante.objects.create(entrega=self.entrega)
        self.entrega.delete()
        self.assertEqual(Comprovante.objects.count(), 0)
