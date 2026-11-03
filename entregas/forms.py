from django import forms

from .models import Comprovante

TAMANHO_MAXIMO_FOTO = 5 * 1024 * 1024
TAMANHO_MAXIMO_ASSINATURA = 300_000
PREFIXO_ASSINATURA = "data:image/png;base64,"


class ComprovanteForm(forms.ModelForm):
    """Comprovante da entrega: foto, assinatura na tela ou os dois."""

    class Meta:
        model = Comprovante
        fields = ["foto", "assinatura"]
        labels = {"foto": "Foto do comprovante", "assinatura": "Assinatura"}
        widgets = {
            "foto": forms.ClearableFileInput(
                attrs={"accept": "image/*", "capture": "environment"}
            ),
            "assinatura": forms.HiddenInput(),
        }

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and foto.size > TAMANHO_MAXIMO_FOTO:
            raise forms.ValidationError("A foto deve ter no máximo 5 MB.")
        return foto

    def clean_assinatura(self):
        assinatura = self.cleaned_data.get("assinatura", "")
        if not assinatura:
            return ""
        if not assinatura.startswith(PREFIXO_ASSINATURA):
            raise forms.ValidationError("Assinatura em formato inválido.")
        if len(assinatura) > TAMANHO_MAXIMO_ASSINATURA:
            raise forms.ValidationError("A assinatura é grande demais.")
        return assinatura

    def clean(self):
        dados = super().clean()
        if not dados.get("foto") and not dados.get("assinatura"):
            raise forms.ValidationError(
                "Envie uma foto do comprovante ou assine na tela."
            )
        return dados
