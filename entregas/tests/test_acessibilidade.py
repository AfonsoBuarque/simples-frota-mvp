from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from entregas.models import Entrega, Usuario


class BarraAcessibilidadeTests(TestCase):
    """A barra aparece em todas as telas, inclusive nas que não exigem login."""

    def _verifica_barra(self, resposta):
        self.assertContains(resposta, 'aria-label="Opções de acessibilidade"')
        self.assertContains(resposta, 'data-acao="alto-contraste" aria-pressed="false"')
        self.assertContains(resposta, 'aria-label="Aumentar tamanho do texto"')
        self.assertContains(resposta, 'aria-label="Diminuir tamanho do texto"')
        self.assertContains(resposta, 'id="aviso-acessibilidade" aria-live="polite"')
        self.assertContains(resposta, "entregas/js/acessibilidade.js")

    def test_login(self):
        self._verifica_barra(self.client.get(reverse("login")))

    def test_pagina_publica(self):
        entrega = Entrega.objects.create(cliente="X", endereco="Y")
        self._verifica_barra(
            self.client.get(reverse("entregas:acompanhar", args=[entrega.token_consulta]))
        )

    def test_telas_logadas(self):
        motorista = Usuario.objects.create_user("m", perfil=Usuario.Perfil.MOTORISTA)
        gerente = Usuario.objects.create_user("g", perfil=Usuario.Perfil.GERENTE)
        self.client.force_login(motorista)
        self._verifica_barra(self.client.get(reverse("entregas:minhas_entregas")))
        self.client.force_login(gerente)
        self._verifica_barra(self.client.get(reverse("entregas:painel")))

    def test_arquivos_estaticos_existem(self):
        self.assertIsNotNone(finders.find("entregas/js/acessibilidade.js"))
        css = open(finders.find("entregas/css/app.css"), encoding="utf-8").read()
        self.assertIn("html.alto-contraste", css)
