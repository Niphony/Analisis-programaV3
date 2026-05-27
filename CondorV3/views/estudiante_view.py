"""
Vista del Estudiante
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import *
from models.models import EstudianteModel


class EstudianteWindow(BaseWindow):
    def __init__(self, root, user):
        nav = [
            ("Inscripción", "", "inscripcion"),
            ("Mi Horario",  "",  "horario"),
            ("Mis Notas",   "", "notas"),
        ]
        super().__init__(root, user, "Portal Estudiante", nav)
        self._switch_view("inscripcion")

    def _load_view(self, key):
        if key == "inscripcion":
            self._view_inscripcion()
        elif key == "horario":
            self._view_horario()
        elif key == "notas":
            self._view_notas()

    # ─── INSCRIPCION ──────────────────────────────────────────────
    def _view_inscripcion(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)

        section_title(frame, "Inscripción de Materias").pack(anchor="w", pady=(0, 16))

        periodo = EstudianteModel.get_periodo_activo()
        if not periodo:
            tk.Label(frame, text="No hay periodo activo actualmente.",
                     font=FONT_LABEL, bg=BG_DARK, fg=WARNING).pack()
            return

        tk.Label(frame, text=f"Periodo: {periodo['nombre']}",
                 font=FONT_LABEL, bg=BG_DARK, fg=FG_MUTED).pack(anchor="w", pady=(0, 12))

        existente = EstudianteModel.tiene_solicitud_pendiente_o_aprobada(
            self.user["id"], periodo["id"]
        )

        if existente:
            estado = existente["estado"]
            color = SUCCESS if estado == "aprobada" else WARNING
            card = card_frame(frame)
            card.pack(fill="x", pady=8)
            tk.Label(card, text=f"Ya tienes una solicitud en estado: {estado.upper()}",
                     font=("Segoe UI", 11, "bold"), bg=BG_PANEL, fg=color).pack(pady=8)
            if estado == "aprobada":
                tk.Label(card,
                         text="Tu horario ha sido asignado. Ve al curso 'Mi Horario' para verlo.",
                         font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack()
            else:
                tk.Label(card,
                         text="Tu solicitud está siendo procesada por el administrativo.",
                         font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack()
            return

        # Mostrar materias disponibles para seleccionar
        info = card_frame(frame)
        info.pack(fill="x", pady=(0, 12))
        tk.Label(info, text="Selecciona las materias que deseas cursar este periodo:",
                 font=FONT_LABEL, bg=BG_PANEL, fg=FG_WHITE).pack(anchor="w")
        tk.Label(info, text="El administrativo te asignará un horario según disponibilidad.",
                 font=FONT_SMALL, bg=BG_PANEL, fg=FG_MUTED).pack(anchor="w")

        materias = EstudianteModel.get_todas_materias()
        self.mat_vars = {}

        # Lista de materias con checkboxes
        list_frame = tk.Frame(frame, bg=BG_DARK)
        list_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(list_frame, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_DARK)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, m in enumerate(materias):
            row_bg = ROW_ODD if i % 2 else ROW_EVEN
            row = tk.Frame(scroll_frame, bg=row_bg, padx=12, pady=8)
            row.pack(fill="x", pady=1)
            var = tk.BooleanVar()
            self.mat_vars[m["id"]] = var
            chk = tk.Checkbutton(
                row, text=f"  {m['codigo']}  –  {m['nombre']}  ({m['creditos']} créd.)",
                variable=var, font=FONT_LABEL, bg=row_bg, fg=FG_WHITE,
                activebackground=row_bg, selectcolor=BG_INPUT,
                relief="flat", anchor="w"
            )
            chk.pack(fill="x")

        # Observaciones
        obs_frame = card_frame(frame, pady=10)
        obs_frame.pack(fill="x", pady=(12, 0))
        tk.Label(obs_frame, text="Observaciones (opcional):", font=FONT_LABEL,
                 bg=BG_PANEL, fg=FG_MUTED).pack(anchor="w")
        self.obs_txt = tk.Text(obs_frame, height=3, font=FONT_INPUT, bg=BG_INPUT,
                               fg=FG_WHITE, insertbackground=FG_WHITE, relief="flat", bd=6)
        self.obs_txt.pack(fill="x", pady=(6, 0))

        btn_row = tk.Frame(frame, bg=BG_DARK)
        btn_row.pack(pady=16, anchor="e")
        primary_btn(btn_row, "Enviar Solicitud",
                    lambda: self._enviar_solicitud(periodo), width=22).pack()

    def _enviar_solicitud(self, periodo):
        seleccionadas = [mid for mid, var in self.mat_vars.items() if var.get()]
        if not seleccionadas:
            messagebox.showwarning("Sin materias", "Debes seleccionar al menos una materia.")
            return
        obs = self.obs_txt.get("1.0", "end").strip()
        try:
            EstudianteModel.crear_solicitud(self.user["id"], periodo["id"], seleccionadas, obs)
            messagebox.showinfo("Solicitud enviada",
                                "Tu solicitud fue enviada correctamente.\n"
                                "El administrativo te asignará un horario próximamente.")
            self._switch_view("inscripcion")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ─── HORARIO ────
    def _view_horario(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)
        section_title(frame, "Mi Horario").pack(anchor="w", pady=(0, 16))

        periodo = EstudianteModel.get_periodo_activo()
        if not periodo:
            tk.Label(frame, text="No hay periodo activo.", font=FONT_LABEL, bg=BG_DARK, fg=FG_MUTED).pack()
            return

        horario = EstudianteModel.get_horario(self.user["id"], periodo["id"])
        if not horario:
            info = card_frame(frame)
            info.pack(fill="x")
            tk.Label(info, text="Aún no tienes horario asignado.",
                     font=("Segoe UI", 11), bg=BG_PANEL, fg=WARNING).pack(pady=10)
            tk.Label(info, text="Espera a que el administrativo procese tu solicitud.",
                     font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack()
            return

        # Contenedor maestro para la tabla y sus barras de scroll
        tabla_container = tk.Frame(frame, bg=BG_DARK)
        tabla_container.pack(fill="both", expand=True, pady=4)

        cols = ("Día", "Hora Inicio", "Hora Fin", "Materia", "Código", "Docente", "Aula")
        tree = ttk.Treeview(tabla_container, columns=cols, show="headings", height=14)
        style_treeview(tree)
        
        widths = [100, 100, 100, 220, 80, 180, 80]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=70, anchor="center" if w <= 100 else "w")

        dias_orden = {"Lunes": 1, "Martes": 2, "Miércoles": 3, "Jueves": 4,
                      "Viernes": 5, "Sábado": 6, "Domingo": 7}
        horario_sorted = sorted(horario,
                                key=lambda r: (dias_orden.get(r["dia_semana"], 9),
                                               str(r["hora_inicio"])))
        for i, r in enumerate(horario_sorted):
            tag = "odd" if i % 2 else "even"
            tree.insert("", "end", values=(
                r["dia_semana"],
                str(r["hora_inicio"])[:5],
                str(r["hora_fin"])[:5],
                r["nombre"], r["codigo"], r["docente"], r["aula"] or "-"
            ), tags=(tag,))
        tree.tag_configure("odd", background=ROW_ODD)
        tree.tag_configure("even", background=ROW_EVEN)

        # Scrollbars (Vertical y Horizontal)
        sb_ver = ttk.Scrollbar(tabla_container, orient="vertical", command=tree.yview)
        sb_hor = ttk.Scrollbar(tabla_container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sb_ver.set, xscrollcommand=sb_hor.set)

        # Ubicación estratégica usando grid para que la barra horizontal quede abajo de todo
        tree.grid(row=0, column=0, sticky="nsew")
        sb_ver.grid(row=0, column=1, sticky="ns")
        sb_hor.grid(row=1, column=0, sticky="ew")

        tabla_container.grid_rowconfigure(0, weight=1)
        tabla_container.grid_columnconfigure(0, weight=1)

        tk.Label(frame, text=f"Total materias inscritas: {len(horario)}",
                 font=FONT_SMALL, bg=BG_DARK, fg=FG_MUTED).pack(anchor="w", pady=4)

    # ─── NOTAS (MODIFICADO PARA MOSTRAR AVANCES INDEPENDIENTES) ───
    def _view_notas(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)
        section_title(frame, "Mis Notas").pack(anchor="w", pady=(0, 4))

        periodo = EstudianteModel.get_periodo_activo()
        if not periodo:
            tk.Label(frame, text="No hay periodo activo.", bg=BG_DARK, fg=FG_MUTED).pack()
            return

        notas = EstudianteModel.get_notas(self.user["id"], periodo["id"])
        if not notas:
            card = card_frame(frame)
            card.pack(fill="x", pady=12)
            tk.Label(card, text="No tienes materias inscritas aún.",
                     font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack(pady=10)
            return

        # Scroll area
        outer, scroll_frame = make_scrollable_frame(frame)
        outer.pack(fill="both", expand=True)

        for n in notas:
            self._nota_card(scroll_frame, n)

    def _nota_card(self, parent, n):
        pub = n["publicado"]
        card = tk.Frame(parent, bg=BG_PANEL, padx=20, pady=14, relief="flat")
        card.pack(fill="x", pady=6)

        hdr = tk.Frame(card, bg=BG_PANEL)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"{n['nombre']}  ({n['codigo']})",
                 font=("Segoe UI", 11, "bold"), bg=BG_PANEL, fg=FG_WHITE).pack(side="left")

        defin = n["nota_definitiva"]
        if defin is not None:
            color = SUCCESS if float(defin) >= 3.0 else ERROR_CLR
            txt_defin = f"Definitiva Acumulada: {float(defin):.2f}"
        else:
            color = FG_MUTED
            txt_defin = "Definitiva: - "

        tk.Label(hdr, text=txt_defin, font=("Segoe UI", 11, "bold"), bg=BG_PANEL, fg=color).pack(side="right")

        sep = tk.Frame(card, bg=ACCENT, height=1)
        sep.pack(fill="x", pady=8)

        grid = tk.Frame(card, bg=BG_PANEL)
        grid.pack(fill="x")

        def corte_col(parent, titulo, notas_vals, pesos_vals, col_start):
            tk.Label(parent, text=titulo, font=("Segoe UI", 9, "bold"),
                     bg=BG_PANEL, fg=ACCENT).grid(row=0, column=col_start, columnspan=2,
                                                    padx=(0, 20), sticky="w")
            total = 0
            for i, (nota, peso) in enumerate(zip(notas_vals, pesos_vals)):
                nota_v = float(nota) if nota is not None else None
                peso_v = float(peso) if peso is not None else 0.0
                
                if nota_v is not None:
                    contrib = nota_v * peso_v / 100
                    total += contrib
                    texto_nota = f"  Nota {i+1}: {nota_v:.1f}  (peso {peso_v:.0f}%)"
                    texto_contrib = f"→ {contrib:.2f}"
                else:
                    texto_nota = f"  Nota {i+1}:  -  (peso {peso_v:.0f}%)"
                    texto_contrib = "→  -"

                r = i + 1
                tk.Label(parent, text=texto_nota, font=FONT_SMALL, bg=BG_PANEL, fg=FG_WHITE).grid(
                    row=r, column=col_start, padx=(0, 10), sticky="w")
                tk.Label(parent, text=texto_contrib, font=FONT_SMALL, bg=BG_PANEL, fg=FG_MUTED).grid(
                    row=r, column=col_start + 1, sticky="w", padx=(0, 20))
            
            tk.Label(parent, text=f"  Subtotal: {total:.2f}",
                     font=("Segoe UI", 9, "bold"), bg=BG_PANEL, fg=SUCCESS).grid(
                row=4, column=col_start, padx=(0, 10), sticky="w")

        corte_col(grid, "1er Corte (35%)",
                  [n["p1_nota1"], n["p1_nota2"], n["p1_nota3"]],
                  [n["p1_peso1"], n["p1_peso2"], n["p1_peso3"]], 0)

        corte_col(grid, "2do Corte (35%)",
                  [n["p2_nota1"], n["p2_nota2"], n["p2_nota3"]],
                  [n["p2_peso1"], n["p2_peso2"], n["p2_peso3"]], 2)

        # 3er corte
        ef = float(n["examen_final"]) if n["examen_final"] is not None else None
        ef_calc = ef if ef is not None else 0.0
        subtotal_p3 = ef_calc * 0.30

        txt_ef = f"  Examen final: {ef:.1f} " if ef is not None else "  Examen final:"

        tk.Label(grid, text="3er Corte (30%)", font=("Segoe UI", 9, "bold"),
                 bg=BG_PANEL, fg=ACCENT).grid(row=0, column=4, columnspan=2, sticky="w", padx=(0, 10))
        tk.Label(grid, text=txt_ef, font=FONT_SMALL, bg=BG_PANEL, fg=FG_WHITE).grid(row=1, column=4, sticky="w")
        tk.Label(grid, text=f"  Subtotal: {subtotal_p3:.2f}",
                 font=("Segoe UI", 9, "bold"), bg=BG_PANEL, fg=SUCCESS).grid(row=4, column=4, sticky="w")

