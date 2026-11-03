import os
import shutil
import tempfile
from io import BytesIO
from unittest import mock

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from entregas.models import Comprovante, Entrega, Usuario

MEDIA_TESTE = tempfile.mkdtemp()


class SaudeTests(TestCase):
    def test_saude_responde_ok_sem_login(self):
        r = self.client.get(reverse("entregas:saude"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok", "banco": "ok"})
        self.assertIn("no-cache", r["Cache-Control"])

    def test_saude_so_aceita_get(self):
        self.assertEqual(self.client.post("/saude/").status_code, 405)


class ConfiguracaoTests(TestCase):
    def test_idioma_e_fuso_do_brasil(self):
        self.assertEqual(settings.LANGUAGE_CODE, "pt-br")
        self.assertEqual(settings.TIME_ZONE, "America/Sao_Paulo")

    def test_mensagens_padrao_em_portugues(self):
        gerente = Usuario.objects.create_user("g", perfil=Usuario.Perfil.GERENTE)
        self.client.force_login(gerente)
        r = self.client.post(reverse("entregas:nova_entrega"), {})
        self.assertContains(r, "Este campo é obrigatório.")

    def test_sessao_de_12_horas(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 43200)


@override_settings(MEDIA_ROOT=MEDIA_TESTE)
class ComprovanteProtegidoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TESTE, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.gerente = Usuario.objects.create_user("g", perfil=Usuario.Perfil.GERENTE)
        self.carlos = Usuario.objects.create_user("carlos", perfil=Usuario.Perfil.MOTORISTA)
        self.marina = Usuario.objects.create_user("marina", perfil=Usuario.Perfil.MOTORISTA)
        self.entrega = Entrega.objects.create(
            cliente="Mercado", endereco="Rua A", motorista=self.carlos,
            status=Entrega.Status.ENTREGUE,
        )
        buf = BytesIO()
        Image.new("RGB", (4, 4), "white").save(buf, "PNG")
        Comprovante.objects.create(
            entrega=self.entrega,
            foto=SimpleUploadedFile("c.png", buf.getvalue(), content_type="image/png"),
            assinatura="data:image/png;base64,AA",
        )
        self.url = reverse("entregas:ver_comprovante", args=[self.entrega.pk])
        self.url_foto = reverse("entregas:foto_comprovante", args=[self.entrega.pk])

    def test_gerente_ve_comprovante_e_foto(self):
        self.client.force_login(self.gerente)
        r = self.client.get(self.url)
        self.assertContains(r, 'alt="Foto do comprovante da entrega para Mercado"')
        self.assertContains(r, 'alt="Assinatura do recebedor da entrega para Mercado"')
        foto = self.client.get(self.url_foto)
        self.assertEqual(foto.status_code, 200)
        self.assertIn("no-store", foto["Cache-Control"])
        b"".join(foto.streaming_content)

    def test_motorista_da_entrega_ve(self):
        self.client.force_login(self.carlos)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_outro_motorista_nao_ve(self):
        self.client.force_login(self.marina)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.get(self.url_foto).status_code, 404)

    def test_sem_login_redireciona(self):
        r = self.client.get(self.url_foto)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])

    def test_painel_linka_comprovante(self):
        self.client.force_login(self.gerente)
        self.assertContains(self.client.get(reverse("entregas:painel")), self.url)

    def test_entrega_sem_comprovante_404(self):
        outra = Entrega.objects.create(cliente="X", endereco="Y", motorista=self.carlos)
        self.client.force_login(self.gerente)
        self.assertEqual(self.client.get(reverse("entregas:ver_comprovante", args=[outra.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("entregas:foto_comprovante", args=[outra.pk])).status_code, 404)

    def test_arquivo_apagado_404(self):
        os.remove(self.entrega.comprovante.foto.path)
        self.client.force_login(self.gerente)
        self.assertEqual(self.client.get(self.url_foto).status_code, 404)


@override_settings(DEBUG=False)
class PopularDemoProducaoTests(TestCase):
    def test_exige_flag(self):
        with self.assertRaises(CommandError):
            call_command("popular_demo")

    @mock.patch.dict(os.environ, {"DEMO_SENHA": "curta"})
    def test_exige_senha_forte(self):
        with self.assertRaises(CommandError):
            call_command("popular_demo", "--producao")

    @mock.patch.dict(os.environ, {"DEMO_SENHA": "SenhaForte-2026"})
    def test_usa_senha_da_variavel(self):
        call_command("popular_demo", "--producao")
        carlos = Usuario.objects.get(username="carlos")
        self.assertTrue(carlos.check_password("SenhaForte-2026"))
        self.assertFalse(carlos.check_password("demo12345"))


class RedirecionamentoHttpsTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[r"^saude/$"])
    def test_http_vai_para_https_exceto_health_check(self):
        r = self.client.get(reverse("login"))
        self.assertEqual(r.status_code, 301)
        self.assertTrue(r["Location"].startswith("https://"))
        self.assertEqual(self.client.get(reverse("entregas:saude")).status_code, 200)


class PaginasDeErroTests(TestCase):
    def test_404_em_portugues(self):
        r = self.client.get("/endereco-que-nao-existe/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "Página não encontrada", status_code=404)
