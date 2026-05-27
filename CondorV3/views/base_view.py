import tkinter as tk
from tkinter import ttk

# Paleta de colores 
BG_DARK    = "#1e1e2e"
BG_PANEL   = "#2a2a3e"
BG_PANEL2  = "#22223a"
BG_INPUT   = "#313145"
BG_TABLE   = "#252535"
FG_WHITE   = "#e0e0ef"
FG_MUTED   = "#8888aa"
ACCENT     = "#7c6af7"
ACCENT_HOV = "#9d8fff"
BTN_FG     = "#ffffff"
ERROR_CLR  = "#f28b82"
SUCCESS    = "#81c995"
WARNING    = "#f9c74f"
SIDEBAR_BG = "#16162a"
SIDEBAR_SEL= "#3a3a5c"
ROW_ODD    = "#252535"
ROW_EVEN   = "#1e1e2e"

FONT_TITLE  = ("Arial", 16, "bold")
FONT_LABEL  = ("Arial", 10)
FONT_INPUT  = ("Arial", 10)
FONT_BTN    = ("Arial", 10, "bold")
FONT_SMALL  = ("Arial", 9)
FONT_TABLE  = ("Arial", 9)
FONT_HEADER = ("Arial", 10, "bold")
FONT_SECTION= ("Arial", 12, "bold")


def style_treeview(tree):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.Treeview",
        background=BG_TABLE, foreground=FG_WHITE,
        fieldbackground=BG_TABLE, rowheight=26,
        font=FONT_TABLE, borderwidth=0)
    style.configure("Dark.Treeview.Heading",
        background=BG_PANEL, foreground=ACCENT,
        font=FONT_HEADER, relief="flat", borderwidth=0)
    style.map("Dark.Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", "#ffffff")])
    tree.configure(style="Dark.Treeview")


def make_scrollable_frame(parent):
    """Retorna (outer_frame, inner_frame) con scrollbar"""
    outer = tk.Frame(parent, bg=BG_DARK)
    canvas = tk.Canvas(outer, bg=BG_DARK, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG_DARK)

    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return outer, inner


def primary_btn(parent, text, command, width=None):
    kwargs = dict(
        text=text, font=FONT_BTN, bg=ACCENT, fg=BTN_FG,
        activebackground=ACCENT_HOV, relief="flat", bd=0,
        cursor="hand2", command=command, padx=14, pady=6
    )
    if width:
        kwargs["width"] = width
    return tk.Button(parent, **kwargs)


def danger_btn(parent, text, command, width=None):
    kwargs = dict(
        text=text, font=FONT_BTN, bg="#c0392b", fg=BTN_FG,
        activebackground="#e74c3c", relief="flat", bd=0,
        cursor="hand2", command=command, padx=14, pady=6
    )
    if width:
        kwargs["width"] = width
    return tk.Button(parent, **kwargs)


def success_btn(parent, text, command, width=None):
    kwargs = dict(
        text=text, font=FONT_BTN, bg="#27ae60", fg=BTN_FG,
        activebackground="#2ecc71", relief="flat", bd=0,
        cursor="hand2", command=command, padx=14, pady=6
    )
    if width:
        kwargs["width"] = width
    return tk.Button(parent, **kwargs)


def section_title(parent, text):
    return tk.Label(parent, text=text, font=FONT_SECTION, bg=BG_DARK, fg=ACCENT)


def card_frame(parent, padx=20, pady=16):
    return tk.Frame(parent, bg=BG_PANEL, padx=padx, pady=pady, relief="flat")


def make_entry(parent, width=30, show=None):
    kwargs = dict(font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                  insertbackground=FG_WHITE, relief="flat", bd=6, width=width)
    if show:
        kwargs["show"] = show
    return tk.Entry(parent, **kwargs)


def make_label(parent, text, muted=False):
    return tk.Label(parent, text=text, font=FONT_LABEL,
                    bg=BG_PANEL, fg=FG_MUTED if muted else FG_WHITE)


class BaseWindow:
    """Ventana base con sidebar de navegación"""
    def __init__(self, root, user, title, nav_items):
        self.root = root
        self.user = user
        self.root.title(f"{title} — {user['nombre']}")
        self.root.geometry("1100x700")
        self.root.configure(bg=BG_DARK)
        self._center_window()
        self.current_view = None
        self._build_layout(nav_items)

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 1100, 700
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_layout(self, nav_items):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=SIDEBAR_BG, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar header
        hdr = tk.Frame(self.sidebar, bg=SIDEBAR_BG, padx=16, pady=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text=self._get_role_text(), font=("Segoe UI", 12, "bold"), bg=SIDEBAR_BG, fg=ACCENT).pack()
        tk.Label(hdr, text=self.user["nombre"], font=("Segoe UI", 10, "bold"),
                 bg=SIDEBAR_BG, fg=FG_WHITE, wraplength=180).pack(pady=(4, 0))
        tk.Label(hdr, text=self.user["rol"].capitalize(), font=FONT_SMALL,
                 bg=SIDEBAR_BG, fg=FG_MUTED).pack()

        # Divisor
        tk.Frame(self.sidebar, bg=BG_PANEL, height=1).pack(fill="x", pady=8)

        # Nav buttons
        self.nav_buttons = {}
        for label, icon, key in nav_items:
            # Se omite visualmente la variable 'icon' para remover los emojis
            btn = tk.Button(
                self.sidebar, text=f"  {label}",
                font=FONT_LABEL, bg=SIDEBAR_BG, fg=FG_WHITE,
                activebackground=SIDEBAR_SEL, relief="flat", bd=0,
                anchor="w", cursor="hand2", padx=16, pady=12,
                command=lambda k=key: self._switch_view(k)
            )
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

        # Spacer + logout
        tk.Frame(self.sidebar, bg=SIDEBAR_BG).pack(fill="y", expand=True)
        tk.Frame(self.sidebar, bg=BG_PANEL, height=1).pack(fill="x", pady=4)
        tk.Button(
            self.sidebar, text="  Cerrar sesión",
            font=FONT_LABEL, bg=SIDEBAR_BG, fg=ERROR_CLR,
            activebackground=SIDEBAR_SEL, relief="flat", bd=0,
            anchor="w", cursor="hand2", padx=16, pady=12,
            command=self._logout
        ).pack(fill="x")

        # Content area
        self.content = tk.Frame(self.root, bg=BG_DARK)
        self.content.pack(side="left", fill="both", expand=True)

    def _get_role_text(self):
        rol = self.user.get("rol", "")
        return {"estudiante": "ESTUDIANTE", "docente": "DOCENTE", "administrativo": "ADMINISTRATIVO"}.get(rol, "USUARIO")

    def _switch_view(self, key):
        # Highlight nav button
        for k, btn in self.nav_buttons.items():
            btn.config(bg=SIDEBAR_SEL if k == key else SIDEBAR_BG)
        # Clear content
        for w in self.content.winfo_children():
            w.destroy()
        self.current_view = key
        self._load_view(key)

    def _load_view(self, key):
        pass 

    def _logout(self):
        self.root.destroy()
        import tkinter as tk2
        new_root = tk2.Tk()
        from views.login_view import LoginWindow
        LoginWindow(new_root)
        new_root.mainloop()