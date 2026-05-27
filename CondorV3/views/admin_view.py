#Menu del administrativo
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import *
from models.models import AdminModel, EstudianteModel


DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]


class AdminWindow(BaseWindow):
    def __init__(self, root, user):
        nav = [
            ("Solicitudes",       "", "solicitudes"),
            ("Horarios Docentes", "", "horarios"),
            ("Registrar Docente", "", "nuevo_docente"),
            ("Historial",         "", "historial"),
        ]
        super().__init__(root, user, "Portal Administrativo", nav)
        self._switch_view("solicitudes")

    def _load_view(self, key):
        if key == "solicitudes":
            self._view_solicitudes()
        elif key == "horarios":
            self._view_horarios_docentes()
        elif key == "nuevo_docente":
            self._view_nuevo_docente()
        elif key == "historial":
            self._view_historial()

    #Solicitudes
    def _view_solicitudes(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)
        section_title(frame, "Solicitudes de Inscripción Pendientes").pack(anchor="w", pady=(0, 16))

        periodo = AdminModel.get_periodo_activo()
        if not periodo:
            tk.Label(frame, text="No hay periodo activo.", bg=BG_DARK, fg=FG_MUTED).pack()
            return

        solicitudes = AdminModel.get_solicitudes_pendientes(periodo["id"])
        if not solicitudes:
            card = card_frame(frame)
            card.pack(fill="x")
            tk.Label(card, text="No hay solicitudes pendientes.",
                     font=FONT_LABEL, bg=BG_PANEL, fg=SUCCESS).pack(pady=12)
            return

        #Tabla de solicitudes
        cols = ("ID", "Estudiante", "Usuario", "Fecha", "Estado")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=8, selectmode="browse")
        style_treeview(tree)
        widths = [50, 220, 100, 160, 90]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center" if w <= 100 else "w")

        for i, s in enumerate(solicitudes):
            tag = "odd" if i % 2 else "even"
            tree.insert("", "end", iid=str(s["id"]), values=(
                s["id"], s["estudiante"], s["username"],
                str(s["fecha_solicitud"])[:16], s["estado"]
            ), tags=(tag,))
        tree.tag_configure("odd", background=ROW_ODD)
        tree.tag_configure("even", background=ROW_EVEN)
        tree.pack(fill="x", pady=(0, 8))

        #Panel de detalle
        sep = tk.Frame(frame, bg=ACCENT, height=1)
        sep.pack(fill="x", pady=8)
        section_title(frame, "Asignar Horario").pack(anchor="w", pady=(0, 8))

        self.detail_frame = tk.Frame(frame, bg=BG_DARK)
        self.detail_frame.pack(fill="both", expand=True)

        def on_select(e):
            sel = tree.selection()
            if sel:
                sol_id = int(sel[0])
                sol = next((s for s in solicitudes if s["id"] == sol_id), None)
                if sol:
                    self._mostrar_detalle_solicitud(self.detail_frame, sol, periodo)

        tree.bind("<<TreeviewSelect>>", on_select)

    def _mostrar_detalle_solicitud(self, parent, sol, periodo):
        for w in parent.winfo_children():
            w.destroy()

        materias = AdminModel.get_materias_solicitud(sol["id"])
        if not materias:
            tk.Label(parent, text="Sin materias en esta solicitud.",
                     bg=BG_DARK, fg=FG_MUTED).pack()
            return

        info = card_frame(parent, pady=10)
        info.pack(fill="x", pady=(0, 10))
        tk.Label(info, text=f"Estudiante: {sol['estudiante']}  ({sol['username']})",
                 font=("Segoe UI", 10, "bold"), bg=BG_PANEL, fg=FG_WHITE).pack(anchor="w")
        tk.Label(info, text="Asigna un curso para cada materia solicitada:",
                 font=FONT_SMALL, bg=BG_PANEL, fg=FG_MUTED).pack(anchor="w", pady=(4, 0))

        outer, scroll_f = make_scrollable_frame(parent)
        outer.pack(fill="both", expand=True)

        self.asig_vars = {}  # materia_id -> IntVar (curso_id)

        for m in materias:
            mcard = tk.Frame(scroll_f, bg=BG_PANEL, padx=14, pady=10)
            mcard.pack(fill="x", pady=4)
            tk.Label(mcard, text=f"Materia: {m['nombre']}  ({m['codigo']})",
                     font=("Segoe UI", 10, "bold"), bg=BG_PANEL, fg=FG_WHITE).pack(anchor="w")

            cursos = AdminModel.get_secciones_disponibles(m["id"], periodo["id"])
            if not cursos:
                tk.Label(mcard, text="Sin cursos disponibles para esta materia.",
                         font=FONT_SMALL, bg=BG_PANEL, fg=WARNING).pack(anchor="w")
                self.asig_vars[m["id"]] = None
                continue

            var = tk.IntVar(value=0)
            self.asig_vars[m["id"]] = var
            # Radio buttons por curso
            for c in cursos:
                txt = (f"  {c['docente']}  |  {c['dia_semana'] or 'Sin día'}  "
                       f"{str(c['hora_inicio'])[:5] if c['hora_inicio'] else ''}-"
                       f"{str(c['hora_fin'])[:5] if c['hora_fin'] else ''}  "
                       f"Aula:{c['aula'] or '-'}  Inscritos:{c['inscritos']}/{c['cupo_max']}")
                tk.Radiobutton(
                    mcard, text=txt, variable=var, value=c["id"],
                    font=FONT_SMALL, bg=BG_PANEL, fg=FG_WHITE,
                    activebackground=BG_PANEL, selectcolor=BG_INPUT
                ).pack(anchor="w", pady=1)

        # Botones aprobar / rechazar
        btn_row = tk.Frame(scroll_f, bg=BG_DARK, pady=12)
        btn_row.pack(fill="x")

        danger_btn(btn_row, "Rechazar",
                   lambda: self._rechazar_solicitud(sol["id"])).pack(side="right", padx=4)
        success_btn(btn_row, "Aprobar y Asignar",
                    lambda: self._aprobar_solicitud(sol, periodo["id"])).pack(side="right", padx=4)

    def _aprobar_solicitud(self, sol, periodo_id):
        asignaciones = []
        for mid, var in self.asig_vars.items():
            if var is None:
                messagebox.showwarning("Sin curso",
                                       f"No hay cursos disponibles para alguna materia. "
                                       f"Considera rechazar la solicitud.")
                return
            cur_id = var.get()
            if cur_id == 0:
                messagebox.showwarning("Incompleto",
                                       "Selecciona un curso para cada materia antes de aprobar.")
                return
            asignaciones.append((mid, cur_id))

        try:
            AdminModel.asignar_horario(sol["id"], sol["estudiante_id"] if "estudiante_id" in sol else self._get_est_id(sol),
                                       periodo_id, asignaciones)
        except Exception:
            # Obtener estudiante_id de la solicitud
            from db.conexion import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT estudiante_id FROM solicitudes_inscripcion WHERE id=%s", (sol["id"],))
                    row = cur.fetchone()
                    est_id = row["estudiante_id"] if row else None
            if est_id:
                AdminModel.asignar_horario(sol["id"], est_id, periodo_id, asignaciones)

        messagebox.showinfo("Aprobado", f"Horario asignado a {sol['estudiante']} exitosamente.")
        self._switch_view("solicitudes")

    def _rechazar_solicitud(self, sol_id):
        win = tk.Toplevel()
        win.title("Rechazar solicitud")
        win.geometry("400x220")
        win.configure(bg=BG_DARK)
        win.grab_set()
        tk.Label(win, text="Motivo del rechazo:", font=FONT_LABEL, bg=BG_DARK, fg=FG_WHITE).pack(pady=12)
        txt = tk.Text(win, height=5, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                      insertbackground=FG_WHITE, relief="flat", bd=6)
        txt.pack(fill="x", padx=20)
        def _do():
            motivo = txt.get("1.0", "end").strip()
            AdminModel.rechazar_solicitud(sol_id, motivo)
            win.destroy()
            messagebox.showinfo("Rechazada", "Solicitud rechazada.")
            self._switch_view("solicitudes")
        danger_btn(win, "Confirmar rechazo", _do).pack(pady=12)

    #Horario de los docentes
    def _view_horarios_docentes(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)
        section_title(frame, "Gestión de Horarios Docentes").pack(anchor="w", pady=(0, 16))

        periodo = AdminModel.get_periodo_activo()
        if not periodo:
            tk.Label(frame, text="No hay periodo activo.", bg=BG_DARK, fg=FG_MUTED).pack()
            return

        #lista docentes | cursos del docente
        paned = tk.PanedWindow(frame, bg=BG_DARK, orient="horizontal", sashwidth=6,
                               sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True)

        #Panel izq – docentes
        left = tk.Frame(paned, bg=BG_DARK, width=260)
        paned.add(left, minsize=220)
        tk.Label(left, text="Docentes", font=FONT_HEADER, bg=BG_DARK, fg=ACCENT).pack(anchor="w", pady=(0, 6))

        docentes = AdminModel.get_todos_docentes()
        doc_cols = ("Nombre", "Usuario")
        self.tree_doc = ttk.Treeview(left, columns=doc_cols, show="headings",
                                      height=20, selectmode="browse")
        style_treeview(self.tree_doc)
        self.tree_doc.heading("Nombre", text="Nombre")
        self.tree_doc.column("Nombre", width=180)
        self.tree_doc.heading("Usuario", text="Usuario")
        self.tree_doc.column("Usuario", width=80)
        for i, d in enumerate(docentes):
            tag = "odd" if i % 2 else "even"
            self.tree_doc.insert("", "end", iid=str(d["id"]),
                                  values=(d["nombre"], d["username"]), tags=(tag,))
        self.tree_doc.tag_configure("odd", background=ROW_ODD)
        self.tree_doc.tag_configure("even", background=ROW_EVEN)
        self.tree_doc.pack(fill="both", expand=True)

        # Panel der – cursos del docente
        right = tk.Frame(paned, bg=BG_DARK)
        paned.add(right, minsize=400)
        self.cur_right = right
        self._periodo_activo = periodo

        self.tree_doc.bind("<<TreeviewSelect>>", self._on_doc_select)
        # Seleccionar primer docente
        if docentes:
            self.tree_doc.selection_set(str(docentes[0]["id"]))

    def _on_doc_select(self, e):
        for w in self.cur_right.winfo_children():
            w.destroy()
        sel = self.tree_doc.selection()
        if not sel:
            return
        doc_id = int(sel[0])
        doc_name = self.tree_doc.item(sel[0])["values"][0]
        periodo = self._periodo_activo

        tk.Label(self.cur_right, text=f"Cursos de {doc_name}",
                 font=FONT_HEADER, bg=BG_DARK, fg=ACCENT).pack(anchor="w", pady=(0, 8))

        cursos = AdminModel.get_secciones_docente(doc_id, periodo["id"])
        cols = ("ID", "Materia", "Día", "H.Inicio", "H.Fin", "Aula")
        tree2 = ttk.Treeview(self.cur_right, columns=cols, show="headings",
                              height=8, selectmode="browse")
        style_treeview(tree2)
        widths2 = [40, 180, 90, 80, 80, 70]
        for col, w in zip(cols, widths2):
            tree2.heading(col, text=col)
            tree2.column(col, width=w, anchor="center" if w <= 90 else "w")
        for i, c in enumerate(cursos):
            tag = "odd" if i % 2 else "even"
            tree2.insert("", "end", iid=str(c["id"]), values=(
                c["id"], c["materia"], c["dia_semana"] or "-",
                str(c["hora_inicio"])[:5] if c["hora_inicio"] else "-",
                str(c["hora_fin"])[:5] if c["hora_fin"] else "-",
                c["aula"] or "-"
            ), tags=(tag,))
        tree2.tag_configure("odd", background=ROW_ODD)
        tree2.tag_configure("even", background=ROW_EVEN)
        tree2.pack(fill="x", pady=(0, 8))

        # Eliminar curso
        btn_del = danger_btn(self.cur_right, "Eliminar curso seleccionado",
                             lambda: self._eliminar_curso(tree2), width=28)
        btn_del.pack(anchor="e", padx=4, pady=(0, 12))

        # Formulario nuevo curso
        sep = tk.Frame(self.cur_right, bg=ACCENT, height=1)
        sep.pack(fill="x", pady=8)
        tk.Label(self.cur_right, text="Nueva Curso",
                 font=FONT_SECTION, bg=BG_DARK, fg=FG_WHITE).pack(anchor="w", pady=(0, 10))

        form = card_frame(self.cur_right, pady=16)
        form.pack(fill="x")

        materias = AdminModel.get_todas_materias()
        mat_opts = [f"{m['codigo']} – {m['nombre']}" for m in materias]
        mat_map = {opt: m["id"] for opt, m in zip(mat_opts, materias)}

        def lrow(text):
            tk.Label(form, text=text, font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED,
                     width=12, anchor="e").pack(side="left", padx=(0, 6))

        row1 = tk.Frame(form, bg=BG_PANEL)
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="Materia:", font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack(side="left")
        mat_var = tk.StringVar()
        cb_mat = ttk.Combobox(row1, textvariable=mat_var, values=mat_opts, state="readonly",
                              font=FONT_INPUT, width=36)
        cb_mat.pack(side="left", padx=8)
        if mat_opts:
            cb_mat.current(0)

        row2 = tk.Frame(form, bg=BG_PANEL)
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="Día:", font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack(side="left")
        dia_var = tk.StringVar(value="Lunes")
        cb_dia = ttk.Combobox(row2, textvariable=dia_var, values=DIAS, state="readonly",
                               font=FONT_INPUT, width=12)
        cb_dia.pack(side="left", padx=8)
        tk.Label(row2, text="Aula:", font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack(side="left", padx=(16, 0))
        e_aula = make_entry(form, width=10)
        e_aula.pack_forget()
        e_aula = tk.Entry(row2, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                          insertbackground=FG_WHITE, relief="flat", bd=4, width=10)
        e_aula.insert(0, "101")
        e_aula.pack(side="left", padx=8)

        row3 = tk.Frame(form, bg=BG_PANEL)
        row3.pack(fill="x", pady=4)
        tk.Label(row3, text="Hora inicio:", font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack(side="left")
        e_hi = tk.Entry(row3, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                        insertbackground=FG_WHITE, relief="flat", bd=4, width=8)
        e_hi.insert(0, "06:00")
        e_hi.pack(side="left", padx=8)
        tk.Label(row3, text="Hora fin:", font=FONT_LABEL, bg=BG_PANEL, fg=FG_MUTED).pack(side="left", padx=(16, 0))
        e_hf = tk.Entry(row3, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                        insertbackground=FG_WHITE, relief="flat", bd=4, width=8)
        e_hf.insert(0, "08:00")
        e_hf.pack(side="left", padx=8)

        lbl_msg = tk.Label(form, text="", font=FONT_SMALL, bg=BG_PANEL, fg=SUCCESS)
        lbl_msg.pack(anchor="w", pady=4)

        def _crear():
            mat_opt = mat_var.get()
            mid = mat_map.get(mat_opt)
            if not mid:
                lbl_msg.config(text="Selecciona una materia", fg=ERROR_CLR)
                return
            hi = e_hi.get().strip()
            hf = e_hf.get().strip()
            aula = e_aula.get().strip()
            try:
                AdminModel.crear_seccion(mid, doc_id, periodo["id"],
                                          dia_var.get(), hi, hf, aula)
                lbl_msg.config(text="Curso creado", fg=SUCCESS)
                self._on_doc_select(None)
            except Exception as ex:
                lbl_msg.config(text=f"{ex}", fg=ERROR_CLR)

        primary_btn(form, "Crear Curso", _crear).pack(anchor="e", pady=(8, 0))

    def _eliminar_curso(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecciona un curso para eliminar.")
            return
        sec_id = int(sel[0])
        if messagebox.askyesno("Confirmar", "¿Eliminar este curso?"):
            AdminModel.eliminar_seccion(sec_id)
            self._on_doc_select(None)

    #Nuevo docente
    def _view_nuevo_docente(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)
        section_title(frame, "Registrar Nuevo Docente").pack(anchor="w", pady=(0, 24))

        card = card_frame(frame, padx=30, pady=24)
        card.pack(fill="x", ipadx=20)

        fields = [
            ("Nombre completo:", "nombre"),
            ("Usuario (login):", "username"),
            ("Email:", "email"),
            ("Contraseña:", "password"),
        ]
        self._new_doc_entries = {}
        for label, key in fields:
            row = tk.Frame(card, bg=BG_PANEL)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, font=FONT_LABEL, bg=BG_PANEL,
                     fg=FG_MUTED, width=18, anchor="e").pack(side="left", padx=(0, 10))
            show = "●" if key == "password" else None
            e = tk.Entry(row, font=FONT_INPUT, bg=BG_INPUT, fg=FG_WHITE,
                         insertbackground=FG_WHITE, relief="flat", bd=6, width=30,
                         **({"show": show} if show else {}))
            e.pack(side="left", ipady=5)
            self._new_doc_entries[key] = e

        self.lbl_doc_msg = tk.Label(card, text="", font=FONT_SMALL, bg=BG_PANEL, fg=SUCCESS)
        self.lbl_doc_msg.pack(pady=8)
        primary_btn(card, "Registrar Docente", self._registrar_docente, width=20).pack(anchor="e")

    def _registrar_docente(self):
        data = {k: e.get().strip() for k, e in self._new_doc_entries.items()}
        if not all(data.values()):
            self.lbl_doc_msg.config(text="Por favor lleno todos lo datos del docente.", fg=ERROR_CLR)
            return
        try:
            AdminModel.registrar_docente(data["username"], data["nombre"],
                                         data["email"], data["password"])
            self.lbl_doc_msg.config(text=f"Docente '{data['nombre']}' registrado exitosamente.", fg=SUCCESS)
            for e in self._new_doc_entries.values():
                e.delete(0, "end")
        except Exception as ex:
            self.lbl_doc_msg.config(text=f"{ex}", fg=ERROR_CLR)

    #Historia
    def _view_historial(self):
        frame = tk.Frame(self.content, bg=BG_DARK, padx=30, pady=20)
        frame.pack(fill="both", expand=True)
        section_title(frame, "Historial de Solicitudes").pack(anchor="w", pady=(0, 16))

        periodo = AdminModel.get_periodo_activo()
        if not periodo:
            tk.Label(frame, text="No hay periodo activo.", bg=BG_DARK, fg=FG_MUTED).pack()
            return

        hist = AdminModel.get_historial_solicitudes(periodo["id"])
        cols = ("ID", "Estudiante", "Usuario", "Fecha", "Estado")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        style_treeview(tree)
        widths = [50, 240, 100, 160, 100]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center" if w <= 110 else "w")

        for i, h in enumerate(hist):
            color = SUCCESS if h["estado"] == "aprobada" else (ERROR_CLR if h["estado"] == "rechazada" else WARNING)
            tag = f"status_{h['estado']}"
            tree.insert("", "end", values=(
                h["id"], h["estudiante"], h["username"],
                str(h["fecha_solicitud"])[:16], h["estado"].upper()
            ), tags=(tag,))
        tree.tag_configure("status_aprobada", foreground=SUCCESS)
        tree.tag_configure("status_rechazada", foreground=ERROR_CLR)
        tree.tag_configure("status_pendiente", foreground=WARNING)

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Resumen
        total = len(hist)
        aprobadas = sum(1 for h in hist if h["estado"] == "aprobada")
        pendientes = sum(1 for h in hist if h["estado"] == "pendiente")
        rechazadas = sum(1 for h in hist if h["estado"] == "rechazada")
        tk.Label(frame,
                 text=f"Total: {total}  |  Aprobadas: {aprobadas}  |  Pendientes: {pendientes}  |  Rechazadas: {rechazadas}",
                 font=FONT_SMALL, bg=BG_DARK, fg=FG_MUTED).pack(side="bottom", anchor="w", pady=4)
