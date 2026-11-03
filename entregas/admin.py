from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Comprovante, Entrega, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Perfil", {"fields": ("perfil",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Perfil", {"fields": ("perfil",)}),)
    list_display = ("username", "first_name", "last_name", "perfil", "is_active")
    list_filter = ("perfil", "is_active")


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "motorista", "status", "motivo_ocorrencia", "prazo")
    list_filter = ("status", "motorista")
    search_fields = ("cliente", "endereco")


@admin.register(Comprovante)
class ComprovanteAdmin(admin.ModelAdmin):
    list_display = ("entrega", "registrado_em")
