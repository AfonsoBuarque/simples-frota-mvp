from django.urls import path

from . import views

app_name = "entregas"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("entregas/", views.minhas_entregas, name="minhas_entregas"),
    path("entregas/<int:pk>/iniciar/", views.iniciar_rota, name="iniciar_rota"),
    path(
        "entregas/<int:pk>/comprovante/",
        views.registrar_comprovante,
        name="registrar_comprovante",
    ),
    path(
        "entregas/<int:pk>/ocorrencia/",
        views.registrar_ocorrencia,
        name="registrar_ocorrencia",
    ),
    path("entregas/<int:pk>/comprovante/ver/", views.ver_comprovante, name="ver_comprovante"),
    path("entregas/<int:pk>/comprovante/foto/", views.foto_comprovante, name="foto_comprovante"),
    path("saude/", views.saude, name="saude"),
    path("painel/", views.painel, name="painel"),
    path("acompanhar/<uuid:token>/", views.acompanhar, name="acompanhar"),
    path("painel/nova/", views.nova_entrega, name="nova_entrega"),
]
