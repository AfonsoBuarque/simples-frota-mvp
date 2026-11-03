// Preferências de acessibilidade: alto contraste e tamanho do texto.
// Carregado no <head> para aplicar a preferência antes da página aparecer.
(function () {
  var raiz = document.documentElement;
  var NIVEIS = [100, 112.5, 125, 140, 160]; // % do tamanho base
  var PADRAO = 1;

  function ler(chave) {
    try { return window.localStorage.getItem(chave); } catch (e) { return null; }
  }
  function gravar(chave, valor) {
    try { window.localStorage.setItem(chave, valor); } catch (e) { /* navegação privada */ }
  }

  var nivel = parseInt(ler("sf-fonte"), 10);
  if (isNaN(nivel) || nivel < 0 || nivel >= NIVEIS.length) nivel = PADRAO;
  var contraste = ler("sf-contraste") === "1";

  function aplicar() {
    raiz.style.fontSize = NIVEIS[nivel] + "%";
    raiz.classList.toggle("alto-contraste", contraste);
  }
  aplicar();

  function anunciar(texto) {
    var aviso = document.getElementById("aviso-acessibilidade");
    if (aviso) aviso.textContent = texto;
  }

  function atualizarBotoes() {
    var botao = document.querySelector('[data-acao="alto-contraste"]');
    if (botao) botao.setAttribute("aria-pressed", contraste ? "true" : "false");
    var menos = document.querySelector('[data-acao="diminuir-fonte"]');
    var mais = document.querySelector('[data-acao="aumentar-fonte"]');
    if (menos) menos.disabled = nivel === 0;
    if (mais) mais.disabled = nivel === NIVEIS.length - 1;
  }

  document.addEventListener("DOMContentLoaded", function () {
    atualizarBotoes();
    document.addEventListener("click", function (e) {
      var alvo = e.target.closest("[data-acao]");
      if (!alvo) return;
      var acao = alvo.getAttribute("data-acao");
      if (acao === "alto-contraste") {
        contraste = !contraste;
        gravar("sf-contraste", contraste ? "1" : "0");
        anunciar(contraste ? "Alto contraste ativado" : "Alto contraste desativado");
      } else if (acao === "aumentar-fonte" && nivel < NIVEIS.length - 1) {
        nivel += 1;
        gravar("sf-fonte", String(nivel));
        anunciar("Texto em " + NIVEIS[nivel] + "%");
      } else if (acao === "diminuir-fonte" && nivel > 0) {
        nivel -= 1;
        gravar("sf-fonte", String(nivel));
        anunciar("Texto em " + NIVEIS[nivel] + "%");
      }
      aplicar();
      atualizarBotoes();
    });
  });
})();
