from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ComprovanteForm
from .models import Entrega, Usuario
from .permissions import perfil_requerido


@login_required
def inicio(request):
    """Leva cada perfil para a sua tela inicial."""
    if request.user.eh_gerente:
        # O painel do gerente entra na próxima PR.
        return redirect("admin:index")
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
