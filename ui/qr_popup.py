import customtkinter as ctk
from ui.theme import COLORS


class QRPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("scan qr code — steam auth")
        self.geometry("520x580")
        self.configure(fg_color=COLORS["bg"])
        self.resizable(False, False)

        # Mantém o popup na frente
        self.attributes("-topmost", True)
        self.transient(parent)

        # Instrução
        self.info_label = ctk.CTkLabel(
            self,
            text="scan with the Steam mobile app to login",
            font=("JetBrains Mono", 12),
            text_color=COLORS["warning"]
        )
        self.info_label.pack(pady=(20, 4))

        self.sub_label = ctk.CTkLabel(
            self,
            text="qr code refreshes automatically when it expires",
            font=("JetBrains Mono", 10),
            text_color=COLORS["text"]
        )
        self.sub_label.pack(pady=(0, 12))

        # Caixa onde o QR ASCII vai ser exibido
        # Usa fonte Courier que tem largura fixa para todos os caracteres
        self.qr_box = ctk.CTkTextbox(
            self,
            fg_color=COLORS["log_bg"],
            text_color="#ffffff",
            font=("Courier", 10),
            border_width=1,
            border_color="#24283b",
            width=480,
            height=460,
            wrap="none"
        )
        self.qr_box.pack(padx=20, pady=(0, 20))

        # Remove espaçamento entre linhas para o QR ficar alinhado
        # spacing1=0 (antes da linha), spacing2=0 (entre linhas), spacing3=0 (depois da linha)
        self.qr_box._textbox.configure(spacing1=0, spacing2=0, spacing3=0)
        # Garante que a fonte interna também seja monoespaçada
        self.qr_box._textbox.configure(font=("Courier", 10, "normal"))
        self.qr_box.configure(state="disabled")

        # Força o foco após criar
        self.after(100, self._force_focus)

    def _force_focus(self):
        """Força o foco e elevação da janela no Linux."""
        self.lift()
        self.focus_force()
        # Mantém topmost por 2 segundos depois permite perder foco
        self.after(2000, lambda: self.attributes("-topmost", False))

    def update_qr(self, qr_text):
        """Atualiza o QR code exibido."""
        if not self.winfo_exists():
            return

        self.qr_box.configure(state="normal")
        self.qr_box.delete("1.0", "end")
        self.qr_box.insert("end", qr_text)
        self.qr_box.configure(state="disabled")
        self.lift()
