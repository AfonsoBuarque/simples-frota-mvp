from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def perfil_requerido(perfil):
    """Exige usuário autenticado com o perfil informado (gerente ou motorista)."""

    def decorador(view):
        @login_required
        @wraps(view)
        def interna(request, *args, **kwargs):
            if request.user.perfil != perfil:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return interna

    return decorador
