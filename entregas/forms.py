from django import forms

from .models import Comprovante, Entrega, Usuario

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
                attrs={
                    "accept": "image/*",
                    "capture": "environment",
                    "class": "entrada-arquivo",
                    "aria-describedby": "ajuda-foto nome-foto",
                }
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


class EntregaForm(forms.ModelForm):
    """Cadastro de entrega pelo gerente, já com o motorista responsável."""

    class Meta:
        model = Entrega
        fields = ["cliente", "endereco", "observacoes", "prazo", "motorista"]
        labels = {
            "cliente": "Cliente",
            "endereco": "Endereço de entrega",
            "observacoes": "Observações",
            "prazo": "Prazo",
            "motorista": "Motorista",
        }
        help_texts = {
            "observacoes": "Opcional. Ex.: ponto de referência ou horário de recebimento.",
            "prazo": "Opcional. Depois desse horário a entrega aparece como atrasada.",
        }
        widgets = {
            "endereco": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
            "prazo": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["motorista"].queryset = Usuario.objects.filter(
            perfil=Usuario.Perfil.MOTORISTA, is_active=True
        ).order_by("first_name", "username")
        self.fields["motorista"].label_from_instance = (
            lambda u: u.get_full_name() or u.username
        )
        self.fields["motorista"].empty_label = "Sem motorista por enquanto"
        self.fields["prazo"].input_formats = ["%Y-%m-%dT%H:%M"]
        # Liga o texto de ajuda ao campo para leitores de tela.
        for nome, campo in self.fields.items():
            if campo.help_text:
                campo.widget.attrs["aria-describedby"] = f"id_{nome}_ajuda"
