from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ComprovanteForm, EntregaForm
from .models import Entrega, Usuario
from .permissions import perfil_requerido


@login_required
def inicio(request):
    """Leva cada perfil para a sua tela inicial."""
    if request.user.eh_gerente:
        return redirect("entregas:painel")
    return redirect("entregas:minhas_entregas")


@perfil_requerido(Usuario.Perfil.MOTORISTA)
def minhas_entregas(request):
    entregas = request.user.entregas.select_related("comprovante")
    abertas = entregas.exclude(status=Entrega.Status.ENTREGUE).order_by("prazo", "criada_em")
    concluidas = entregas.filter(status=Entrega.Status.ENTREGUE).order_by(
        "-atualizada_em"
    )[:5]
    return render(
        request,
        "entregas/minhas_entregas.html",
        {"abertas": abertas, "concluidas": concluidas},
    )


@perfil_requerido(Usuario.Perfil.MOTORISTA)
@require_POST
def iniciar_rota(request, pk):
    entrega = get_object_or_404(Entrega, pk=pk, motorista=request.user)
    if entrega.status == Entrega.Status.PENDENTE:
        entrega.status = Entrega.Status.EM_ROTA
        entrega.save(update_fields=["status", "atualizada_em"])
        messages.success(request, f"Rota iniciada para {entrega.cliente}.")
    return redirect("entregas:minhas_entregas")


@perfil_requerido(Usuario.Perfil.MOTORISTA)
def registrar_comprovante(request, pk):
    entrega = get_object_or_404(Entrega, pk=pk, motorista=request.user)

    if entrega.status == Entrega.Status.ENTREGUE:
        messages.info(request, "Esta entrega já foi concluída.")
        return redirect("entregas:minhas_entregas")
    if entrega.status == Entrega.Status.PENDENTE:
        messages.error(request, "Inicie a rota antes de registrar o comprovante.")
        return redirect("entregas:minhas_entregas")

    if request.method == "POST":
        form = ComprovanteForm(request.POST, request.FILES)
    else:
        form = ComprovanteForm()
    if form.is_bound and form.is_valid():
        with transaction.atomic():
            comprovante = form.save(commit=False)
            comprovante.entrega = entrega
            comprovante.save()
            entrega.status = Entrega.Status.ENTREGUE
            entrega.save(update_fields=["status", "atualizada_em"])
        messages.success(request, f"Entrega para {entrega.cliente} concluída.")
        return redirect("entregas:minhas_entregas")

    return render(
        request, "entregas/registrar_comprovante.html", {"entrega": entrega, "form": form}
    )


FILTROS_PAINEL = {
    "todas": "Todas",
    "atrasadas": "Atrasadas",
    Entrega.Status.PENDENTE: "Pendentes",
    Entrega.Status.EM_ROTA: "Em rota",
    Entrega.Status.ENTREGUE: "Entregues",
}


@perfil_requerido(Usuario.Perfil.GERENTE)
def painel(request):
    agora = timezone.now()
    filtro_atraso = Q(prazo__lt=agora) & ~Q(status=Entrega.Status.ENTREGUE)
    todas = Entrega.objects.select_related("motorista", "comprovante")

    contagem = todas.aggregate(
        total=Count("id"),
        pendentes=Count("id", filter=Q(status=Entrega.Status.PENDENTE)),
        em_rota=Count("id", filter=Q(status=Entrega.Status.EM_ROTA)),
        entregues=Count("id", filter=Q(status=Entrega.Status.ENTREGUE)),
        atrasadas=Count("id", filter=filtro_atraso),
    )

    filtro = request.GET.get("status", "todas")
    if filtro not in FILTROS_PAINEL:
        filtro = "todas"
    entregas = todas
    if filtro == "atrasadas":
        entregas = todas.filter(filtro_atraso)
    elif filtro != "todas":
        entregas = todas.filter(status=filtro)

    return render(
        request,
        "entregas/painel.html",
        {
            "entregas": entregas,
            "contagem": contagem,
            "filtros": FILTROS_PAINEL,
            "filtro": filtro,
        },
    )


@perfil_requerido(Usuario.Perfil.GERENTE)
def nova_entrega(request):
    if request.method == "POST":
        form = EntregaForm(request.POST)
        if form.is_valid():
            entrega = form.save()
            messages.success(request, f"Entrega para {entrega.cliente} cadastrada.")
            return redirect("entregas:painel")
    else:
        form = EntregaForm()
    return render(request, "entregas/nova_entrega.html", {"form": form})
