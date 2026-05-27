import tkinter as tk
from tkinter import ttk, messagebox
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.models import AuthModel


BG_DARK    = "#1e1e2e"
BG_PANEL   = "#2a2a3e"
BG_INPUT   = "#313145"
FG_WHITE   = "#e0e0ef"
FG_MUTED   = "#8888aa"
ACCENT     = "#1e1e2e"
ACCENT_HOV = "#3BA3A3"
BTN_FG     = "#ffffff"
ERROR_CLR  = "#f28b82"
SUCCESS    = "#81c995"

FONT_TITLE  = ("Arial", 22, "bold")
FONT_LABEL  = ("Arial", 10)
FONT_INPUT  = ("Arial", 11)
FONT_BTN    = ("Arial", 11, "bold")
FONT_SMALL  = ("Arial", 9)


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Académica")
        self.root.geometry("460x540")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 460, 540
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Contenedor principal
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(expand=True, fill="both", padx=40, pady=40)

        # Encabezado de texto
        tk.Label(main, text="Condor", font=FONT_TITLE, bg=BG_DARK, fg=FG_WHITE).pack(pady=(20, 0))
        tk.Label(main, text="Por favor ingrese su usuario y contraseña",
                 font=FONT_SMALL, bg=BG_DARK, fg=FG_MUTED).pack(pady=(4, 30))

        # Card de login
        card = tk.Frame(main, bg=BG_PANEL, padx=30, pady=30, relief="flat")
        card.pack(fill="x")

        # Usuario
        tk.Label(card, text="Usuario", font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED, anchor="w").pack(fill="x")
        self.entry_user = tk.Entry(card, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                                   insertbackground=FG_WHITE, relief="flat", bd=8)
        self.entry_user.pack(fill="x", pady=(4, 16), ipady=6)

        # Contraseña
        tk.Label(card, text="Contraseña", font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED, anchor="w").pack(fill="x")
        self.entry_pass = tk.Entry(card, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                                   insertbackground=FG_WHITE, relief="flat", bd=8, show="●")
        self.entry_pass.pack(fill="x", pady=(4, 24), ipady=6)

        # Mensaje de error
        self.lbl_error = tk.Label(card, text="", font=FONT_SMALL, bg=BG_PANEL, fg=ERROR_CLR)
        self.lbl_error.pack(pady=(0, 8))

        # Botón ingresar
        self.btn_login = tk.Button(
            card, text="Ingresar", font=FONT_BTN,
            bg=ACCENT, fg=BTN_FG, activebackground=ACCENT_HOV,
            relief="flat", bd=0, cursor="hand2",
            command=self._do_login
        )
        self.btn_login.pack(fill="x", ipady=10)

        # Bind Enter
        self.root.bind("<Return>", lambda e: self._do_login())
        self.entry_user.focus()

    def _do_login(self):
        user = self.entry_user.get().strip()
        pwd  = self.entry_pass.get().strip()
        if not user or not pwd:
            self.lbl_error.config(text="No se ingreso ningun usuario o contraseña")
            return

        self.lbl_error.config(text="")
        result = AuthModel.login(user, pwd)
        if result:
            self.root.destroy()
            self._abrir_dashboard(result)
        else:
            self.lbl_error.config(text="Usuario o contraseña incorrectos")
            self.entry_pass.delete(0, "end")

    def _abrir_dashboard(self, user):
        new_root = tk.Tk()
        rol = user["rol"]
        if rol == "estudiante":
            from views.estudiante_view import EstudianteWindow
            EstudianteWindow(new_root, user)
        elif rol == "docente":
            from views.docente_view import DocenteWindow
            DocenteWindow(new_root, user)
        elif rol == "administrativo":
            from views.admin_view import AdminWindow
            AdminWindow(new_root, user)
        new_root.mainloop()