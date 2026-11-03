// Captura de assinatura na tela. A foto continua disponível como alternativa.
(function () {
  var canvas = document.getElementById("area-assinatura");
  if (!canvas) return;
  var campo = document.getElementById("id_assinatura");
  var limpar = document.getElementById("limpar-assinatura");
  var ctx = canvas.getContext("2d");
  var desenhando = false;
  var temTraco = false;

  ctx.lineWidth = 3;
  ctx.lineCap = "round";
  ctx.strokeStyle = "#1a1a1a";

  function posicao(evento) {
    var r = canvas.getBoundingClientRect();
    return {
      x: (evento.clientX - r.left) * (canvas.width / r.width),
      y: (evento.clientY - r.top) * (canvas.height / r.height),
    };
  }

  canvas.addEventListener("pointerdown", function (e) {
    desenhando = true;
    canvas.setPointerCapture(e.pointerId);
    var p = posicao(e);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    e.preventDefault();
  });

  canvas.addEventListener("pointermove", function (e) {
    if (!desenhando) return;
    var p = posicao(e);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    temTraco = true;
  });

  function terminar() {
    if (!desenhando) return;
    desenhando = false;
    if (temTraco) campo.value = canvas.toDataURL("image/png");
  }
  canvas.addEventListener("pointerup", terminar);
  canvas.addEventListener("pointercancel", terminar);

  limpar.addEventListener("click", function () {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    campo.value = "";
    temTraco = false;
  });
})();

// Mostra o nome da foto escolhida, já que o campo nativo fica oculto.
(function () {
  var entrada = document.getElementById("id_foto");
  var nome = document.getElementById("nome-foto");
  if (!entrada || !nome) return;
  entrada.addEventListener("change", function () {
    nome.textContent = entrada.files.length
      ? "Foto selecionada: " + entrada.files[0].name
      : "Nenhuma foto selecionada";
  });
})();
