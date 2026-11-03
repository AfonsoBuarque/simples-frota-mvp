import base64
from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from entregas.models import Comprovante, Entrega, Usuario

ASSINATURA = "data:image/png;base64," + base64.b64encode(b"x" * 50).decode()


def foto_valida(nome="canhoto.png"):
    buf = BytesIO()
    Image.new("RGB", (4, 4), "white").save(buf, "PNG")
    return SimpleUploadedFile(nome, buf.getvalue(), content_type="image/png")


class BaseViewTest(TestCase):
    def setUp(self):
        self.gerente = Usuario.objects.create_user("gerente", password="x12345678", perfil=Usuario.Perfil.GERENTE)
        self.carlos = Usuario.objects.create_user("carlos", password="x12345678", perfil=Usuario.Perfil.MOTORISTA)
        self.marina = Usuario.objects.create_user("marina", password="x12345678", perfil=Usuario.Perfil.MOTORISTA)
        self.entrega = Entrega.objects.create(cliente="Mercado", endereco="Rua A, 1", motorista=self.carlos)


class AcessoTests(BaseViewTest):
    def test_anonimo_vai_para_login(self):
        r = self.client.get(reverse("entregas:minhas_entregas"))
        self.assertRedirects(r, f"{reverse('login')}?next={reverse('entregas:minhas_entregas')}")

    def test_login_page_renderiza(self):
        r = self.client.get(reverse("login"))
        self.assertContains(r, 'lang="pt-BR"')
        self.assertContains(r, "Entrar")

    def test_inicio_motorista(self):
        self.client.force_login(self.carlos)
        self.assertRedirects(self.client.get(reverse("entregas:inicio")), reverse("entregas:minhas_entregas"))

    def test_inicio_gerente(self):
        self.client.force_login(self.gerente)
        r = self.client.get(reverse("entregas:inicio"))
        self.assertRedirects(r, reverse("entregas:painel"))

    def test_gerente_nao_acessa_tela_do_motorista(self):
        self.client.force_login(self.gerente)
        self.assertEqual(self.client.get(reverse("entregas:minhas_entregas")).status_code, 403)

    def test_logout_por_post(self):
        self.client.force_login(self.carlos)
        r = self.client.post(reverse("logout"))
        self.assertRedirects(r, reverse("login"))


class MinhasEntregasTests(BaseViewTest):
    def test_lista_apenas_as_do_motorista(self):
        Entrega.objects.create(cliente="Outra", endereco="Z", motorista=self.marina)
        self.client.force_login(self.carlos)
        r = self.client.get(reverse("entregas:minhas_entregas"))
        self.assertContains(r, "Mercado")
        self.assertNotContains(r, "Outra")

    def test_atrasada_tem_texto(self):
        self.entrega.prazo = timezone.now() - timedelta(hours=1)
        self.entrega.save()
        self.client.force_login(self.carlos)
        self.assertContains(self.client.get(reverse("entregas:minhas_entregas")), "Atrasada")

    def test_vazio_e_concluidas(self):
        self.entrega.status = Entrega.Status.ENTREGUE
        self.entrega.save()
        self.client.force_login(self.carlos)
        r = self.client.get(reverse("entregas:minhas_entregas"))
        self.assertContains(r, "Nenhuma entrega em aberto")
        self.assertContains(r, "Concluídas recentemente")


class IniciarRotaTests(BaseViewTest):
    def test_inicia_rota(self):
        self.client.force_login(self.carlos)
        r = self.client.post(reverse("entregas:iniciar_rota", args=[self.entrega.pk]))
        self.assertRedirects(r, reverse("entregas:minhas_entregas"))
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.EM_ROTA)

    def test_get_nao_permitido(self):
        self.client.force_login(self.carlos)
        self.assertEqual(self.client.get(reverse("entregas:iniciar_rota", args=[self.entrega.pk])).status_code, 405)

    def test_outro_motorista_recebe_404(self):
        self.client.force_login(self.marina)
        self.assertEqual(self.client.post(reverse("entregas:iniciar_rota", args=[self.entrega.pk])).status_code, 404)
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.PENDENTE)


@override_settings(MEDIA_ROOT="/tmp/simples_frota_test_media")
class ComprovanteTests(BaseViewTest):
    def setUp(self):
        super().setUp()
        self.entrega.status = Entrega.Status.EM_ROTA
        self.entrega.save()
        self.url = reverse("entregas:registrar_comprovante", args=[self.entrega.pk])
        self.client.force_login(self.carlos)

    def test_get_renderiza_formulario(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Foto do comprovante")
        self.assertContains(r, "Assinatura na tela")

    def test_pendente_redireciona(self):
        self.entrega.status = Entrega.Status.PENDENTE
        self.entrega.save()
        self.assertRedirects(self.client.get(self.url), reverse("entregas:minhas_entregas"))

    def test_ja_entregue_redireciona(self):
        self.entrega.status = Entrega.Status.ENTREGUE
        self.entrega.save()
        self.assertRedirects(self.client.get(self.url), reverse("entregas:minhas_entregas"))

    def test_assinatura_conclui_entrega(self):
        r = self.client.post(self.url, {"assinatura": ASSINATURA})
        self.assertRedirects(r, reverse("entregas:minhas_entregas"))
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.ENTREGUE)
        self.assertTrue(Comprovante.objects.filter(entrega=self.entrega).exists())

    def test_foto_conclui_entrega(self):
        self.client.post(self.url, {"foto": foto_valida()})
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.ENTREGUE)

    def test_sem_nada_mostra_erro(self):
        r = self.client.post(self.url, {})
        self.assertContains(r, "Envie uma foto do comprovante ou assine na tela.")
        self.entrega.refresh_from_db()
        self.assertEqual(self.entrega.status, Entrega.Status.EM_ROTA)

    def test_assinatura_invalida(self):
        r = self.client.post(self.url, {"assinatura": "javascript:alert(1)"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Comprovante.objects.exists())

    def test_assinatura_grande_demais(self):
        r = self.client.post(self.url, {"assinatura": "data:image/png;base64," + "A" * 300_001})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Comprovante.objects.exists())

    def test_foto_grande_demais(self):
        # PNG válido com dados extras no fim, para passar da validação de imagem
        conteudo = foto_valida().read() + b"\0" * (5 * 1024 * 1024)
        grande = SimpleUploadedFile("g.png", conteudo, content_type="image/png")
        r = self.client.post(self.url, {"foto": grande})
        self.assertContains(r, "A foto deve ter no máximo 5 MB.")
        self.assertFalse(Comprovante.objects.exists())

    def test_arquivo_que_nao_e_imagem(self):
        falso = SimpleUploadedFile("a.png", b"nao sou imagem", content_type="image/png")
        r = self.client.post(self.url, {"foto": falso})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Comprovante.objects.exists())

    def test_outro_motorista_404(self):
        self.client.force_login(self.marina)
        self.assertEqual(self.client.get(self.url).status_code, 404)


class PopularDemoTests(TestCase):
    @override_settings(DEBUG=True)
    def test_cria_dados_e_e_idempotente(self):
        call_command("popular_demo")
        call_command("popular_demo")
        self.assertEqual(Usuario.objects.count(), 3)
        self.assertEqual(Entrega.objects.count(), 6)
        self.assertEqual(Comprovante.objects.count(), 1)
        call_command("popular_demo", "--reset")
        self.assertEqual(Entrega.objects.count(), 6)

    @override_settings(DEBUG=False)
    def test_bloqueado_sem_debug(self):
        with self.assertRaises(CommandError):
            call_command("popular_demo")
