"""
Vista del Docente
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import *
from models.models import DocenteModel, EstudianteModel


class DocenteWindow(BaseWindow):
    def __init__(self, root, user):
        nav = [
            ("Mis Cursos",   "", "cursos"),
            ("Ingresar Notas", "", "notas"),
        ]
        super().__init__(root, user, "Portal Docente", nav)
        self.seccion_seleccionada = None
        self._switch_view("cursos")

    def _load_view(self, key):
        if key == "cursos":
            self._view_cursos()
        elif key == "notas":
            self._view_notas()

    # ─── CURSOS ──────────────────────────────────────────────────
    def _view_cursos(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)
        section_title(frame, "Mis Cursos").pack(anchor="w", pady=(0, 16))

        periodo = EstudianteModel.get_periodo_activo()
        if not periodo:
            tk.Label(frame, text="No hay periodo activo.", bg=BG_DARK, fg=FG_MUTED,
                     font=FONT_LABEL).pack()
            return

        secciones = DocenteModel.get_secciones_docente(self.user["id"], periodo["id"])
        if not secciones:
            card = card_frame(frame)
            card.pack(fill="x")
            tk.Label(card, text="No tienes scursos asignados en este periodo.",
                     font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack(pady=10)
            return

        # Tabla de secciones
        cols = ("Materia", "Código", "Día", "Hora Inicio", "Hora Fin", "Aula", "Inscritos")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=8, selectmode="browse")
        style_treeview(tree)
        widths = [220, 80, 100, 100, 100, 80, 80]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center" if w <= 100 else "w")

        self._secciones_data = secciones
        for i, s in enumerate(secciones):
            tag = "odd" if i % 2 else "even"
            tree.insert("", "end", iid=str(s["id"]), values=(
                s["materia"], s["codigo"],
                s["dia_semana"] or "-",
                str(s["hora_inicio"])[:5] if s["hora_inicio"] else "-",
                str(s["hora_fin"])[:5] if s["hora_fin"] else "-",
                s["aula"] or "-", s["inscritos"]
            ), tags=(tag,))
        tree.tag_configure("odd", background=ROW_ODD)
        tree.tag_configure("even", background=ROW_EVEN)
        tree.pack(fill="x", pady=(0, 12))

        # Panel de inscritos
        tk.Frame(frame, bg=ACCENT, height=1).pack(fill="x", pady=8)
        section_title(frame, "Lista de Inscritos").pack(anchor="w", pady=(0, 8))

        cols2 = ("Estudiante", "Usuario")
        self.tree_inscritos = ttk.Treeview(frame, columns=cols2, show="headings", height=10)
        style_treeview(self.tree_inscritos)
        self.tree_inscritos.heading("Estudiante", text="Nombre")
        self.tree_inscritos.column("Estudiante", width=280)
        self.tree_inscritos.heading("Usuario", text="Usuario")
        self.tree_inscritos.column("Usuario", width=140)
        self.tree_inscritos.pack(fill="x")
        self.lbl_inscritos_count = tk.Label(frame, text="", font=FONT_SMALL,
                                             bg=BG_DARK, fg=FG_MUTED)
        self.lbl_inscritos_count.pack(anchor="w", pady=4)

        def on_select(e):
            sel = tree.selection()
            if sel:
                sec_id = int(sel[0])
                self.seccion_seleccionada = sec_id
                self._cargar_inscritos(sec_id)

        tree.bind("<<TreeviewSelect>>", on_select)
        # Auto-seleccionar primera
        if secciones:
            first = str(secciones[0]["id"])
            tree.selection_set(first)
            self.seccion_seleccionada = secciones[0]["id"]
            self._cargar_inscritos(secciones[0]["id"])

    def _cargar_inscritos(self, seccion_id):
        for row in self.tree_inscritos.get_children():
            self.tree_inscritos.delete(row)
        inscritos = DocenteModel.get_inscritos_seccion(seccion_id)
        for i, est in enumerate(inscritos):
            tag = "odd" if i % 2 else "even"
            self.tree_inscritos.insert("", "end", values=(est["estudiante"], est["username"]), tags=(tag,))
            self.tree_inscritos.tag_configure("odd", background=ROW_ODD)
            self.tree_inscritos.tag_configure("even", background=ROW_EVEN)
        self.lbl_inscritos_count.config(text=f"Total inscritos: {len(inscritos)}")

    # ─── NOTAS ───────────────────────────────────────────────────
    def _view_notas(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)
        section_title(frame, "Ingresar / Editar Notas").pack(anchor="w", pady=(0, 4))

        periodo = EstudianteModel.get_periodo_activo()
        if not periodo:
            tk.Label(frame, text="No hay periodo activo.", bg=BG_DARK, fg=FG_MUTED).pack()
            return

        secciones = DocenteModel.get_secciones_docente(self.user["id"], periodo["id"])
        if not secciones:
            tk.Label(frame, text="No tienes cursos asignados.", font=FONT_LABEL,
                     bg=BG_DARK, fg=FG_MUTED).pack(pady=20)
            return

        # Selector de curso
        sel_frame = card_frame(frame, pady=12)
        sel_frame.pack(fill="x", pady=(0, 14))

        tk.Label(sel_frame, text="Sección:", font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack(side="left")
        self.sec_var = tk.StringVar()
        sec_opts = [f"{s['materia']} – {s['dia_semana'] or 'Sin día'} {str(s['hora_inicio'])[:5] if s['hora_inicio'] else ''}" for s in secciones]
        self.sec_map = {opt: s["id"] for opt, s in zip(sec_opts, secciones)}

        combo = ttk.Combobox(sel_frame, textvariable=self.sec_var, values=sec_opts,
                             state="readonly", font=FONT_INPUT, width=44)
        combo.pack(side="left", padx=(8, 12))
        combo.current(0)

        primary_btn(sel_frame, "Cargar estudiantes",
                    self._cargar_estudiantes_notas, width=20).pack(side="left")

        # Area de notas (scroll)
        self.notas_outer = tk.Frame(frame, bg=BG_DARK)
        self.notas_outer.pack(fill="both", expand=True)
        self._cargar_estudiantes_notas()

    def _cargar_estudiantes_notas(self):
        for w in self.notas_outer.winfo_children():
            w.destroy()

        sel_text = self.sec_var.get()
        sec_id = self.sec_map.get(sel_text)
        if not sec_id:
            return

        inscritos = DocenteModel.get_inscritos_seccion(sec_id)
        if not inscritos:
            tk.Label(self.notas_outer, text="Sin estudiantes inscritos en este curso.",
                     font=FONT_LABEL, bg=BG_DARK, fg=FG_MUTED).pack(pady=20)
            return

        outer, scroll_f = make_scrollable_frame(self.notas_outer)
        outer.pack(fill="both", expand=True)

        self._nota_entries = []
        for est in inscritos:
            self._nota_card_docente(scroll_f, est, sec_id)

        # Botón publicar
        btn_row = tk.Frame(scroll_f, bg=BG_DARK, pady=12)
        btn_row.pack(fill="x")
        success_btn(btn_row, "Publicar todas las notas de este curso",
                    lambda: self._publicar(sec_id)).pack(side="right", padx=4)

    def _nota_card_docente(self, parent, est, sec_id):
        card = tk.Frame(parent, bg=BG_PANEL, padx=16, pady=12, relief="flat")
        card.pack(fill="x", pady=5)

        tk.Label(card, text=f"{est['estudiante']}  ({est['username']})",
                 font=("Segoe UI", 10, "bold"), bg=BG_PANEL, fg=FG_WHITE).pack(anchor="w", pady=(0, 10))

        entries = {}

        def row_notas(parent, titulo, keys_nota, keys_peso):
            f = tk.Frame(parent, bg=BG_PANEL)
            f.pack(fill="x", pady=4)
            tk.Label(f, text=titulo, font=("Segoe UI", 9, "bold"),
                     bg=BG_PANEL, fg=ACCENT, width=18, anchor="w").grid(row=0, column=0, sticky="w")

            headers = ["Nota 1", "Peso%", "Nota 2", "Peso%", "Nota 3", "Peso%"]
            for col, h in enumerate(headers, 1):
                tk.Label(f, text=h, font=FONT_SMALL, bg=BG_PANEL, fg=FG_MUTED,
                         width=7, anchor="center").grid(row=1, column=col, padx=3)

            for i, (kn, kp) in enumerate(zip(keys_nota, keys_peso)):
                col_n = 1 + i * 2
                col_p = col_n + 1
                en = tk.Entry(f, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                              insertbackground=FG_WHITE, relief="flat", bd=4, width=7)
                ep = tk.Entry(f, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                              insertbackground=FG_WHITE, relief="flat", bd=4, width=7)
                en.grid(row=2, column=col_n, padx=3, pady=2)
                ep.grid(row=2, column=col_p, padx=3, pady=2)
                
                val_n = est.get(kn) or 0
                val_p = est.get(kp) or 0
                en.insert(0, str(val_n))
                ep.insert(0, str(val_p))
                entries[kn] = en
                entries[kp] = ep
            return f

        row_notas(card, "1er Corte (35%)",
                  ["p1_nota1","p1_nota2","p1_nota3"],
                  ["p1_peso1","p1_peso2","p1_peso3"])

        row_notas(card, "2do Corte (35%)",
                  ["p2_nota1","p2_nota2","p2_nota3"],
                  ["p2_peso1","p2_peso2","p2_peso3"])

        # 3er corte
        f3 = tk.Frame(card, bg=BG_PANEL)
        f3.pack(fill="x", pady=4)
        tk.Label(f3, text="3er Corte (30%)", font=("Segoe UI", 9, "bold"),
                 bg=BG_PANEL, fg=ACCENT, width=18, anchor="w").grid(row=0, column=0, sticky="w")
        
        tk.Label(f3, text="Examen Final:", font=FONT_LABEL, bg=BG_PANEL, fg=FG_WHITE).grid(row=0, column=1, padx=4)
        
        e_ef = tk.Entry(f3, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                        insertbackground=FG_WHITE, relief="flat", bd=4, width=8)
        e_ef.insert(0, str(est.get("examen_final") or 0))
        e_ef.grid(row=0, column=2, padx=4, pady=2)
        entries["examen_final"] = e_ef

        # Botón guardar individual
        btn_row = tk.Frame(card, bg=BG_PANEL)
        btn_row.pack(anchor="e", pady=(8, 0))
        lbl_result = tk.Label(btn_row, text="", font=FONT_SMALL, bg=BG_PANEL, fg=SUCCESS)
        lbl_result.pack(side="left", padx=8)
        primary_btn(btn_row, "Guardar",
                    lambda e=entries, iid=est["inscripcion_id"], lbl=lbl_result:
                    self._guardar_notas(e, iid, lbl), width=14).pack(side="right")

    def _guardar_notas(self, entries, inscripcion_id, lbl_result):
        try:
            datos = {}
            float_keys = [
                "p1_nota1","p1_nota2","p1_nota3",
                "p1_peso1","p1_peso2","p1_peso3",
                "p2_nota1","p2_nota2","p2_nota3",
                "p2_peso1","p2_peso2","p2_peso3",
                "examen_final"
            ]
            for k in float_keys:
                raw = entries[k].get().strip()
                val = float(raw) if raw else 0.0
                datos[k] = val
            
            #Validacion de las notas
            nota_keys = ["p1_nota1","p1_nota2","p1_nota3","p2_nota1","p2_nota2","p2_nota3",
                         "examen_final"]
            for k in nota_keys:
                if not (0 <= datos[k] <= 50):
                    lbl_result.config(text="las notas deben estar en un valor de 0 a 50", fg=ERROR_CLR)
                    return

            ok, msg = DocenteModel.guardar_notas(inscripcion_id, datos)
            if ok:
                lbl_result.config(text=f"{msg}", fg=SUCCESS)
            else:
                lbl_result.config(text=f"{msg}", fg=ERROR_CLR)
        except ValueError:
            lbl_result.config(text="Ingresa solo números", fg=ERROR_CLR)
        except Exception as e:
            lbl_result.config(text=f"{e}", fg=ERROR_CLR)

    def _publicar(self, sec_id):
        if messagebox.askyesno("Publicar notas",
                               "¿Seguro que deseas publicar sus notas de este curso?"):
            DocenteModel.publicar_notas(sec_id)
            messagebox.showinfo("Publicadas", "Notas publicadas exitosamente.")