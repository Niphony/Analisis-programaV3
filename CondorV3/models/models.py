import hashlib
from db.conexion import get_connection


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Autentificacion del usuario
class AuthModel:
    @staticmethod
    def login(username, password):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, rol, nombre FROM usuarios "
                    "WHERE username=%s AND password_hash=%s AND activo=TRUE",
                    (username, hash_password(password))
                )
                return cur.fetchone()

    @staticmethod
    def cambiar_password(user_id, nueva):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE usuarios SET password_hash=%s WHERE id=%s",
                    (hash_password(nueva), user_id)
                )
            conn.commit()


# ─────────────────────────────────────────────
# ESTUDIANTE
# ─────────────────────────────────────────────
class EstudianteModel:
    @staticmethod
    def get_periodo_activo():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre FROM periodos WHERE activo=TRUE LIMIT 1")
                return cur.fetchone()

    @staticmethod
    def tiene_solicitud_pendiente_o_aprobada(estudiante_id, periodo_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, estado FROM solicitudes_inscripcion "
                    "WHERE estudiante_id=%s AND periodo_id=%s AND estado IN ('pendiente','aprobada')",
                    (estudiante_id, periodo_id)
                )
                return cur.fetchone()

    @staticmethod
    def get_todas_materias():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, codigo, nombre, creditos FROM materias WHERE activa=TRUE ORDER BY codigo")
                return cur.fetchall()

    @staticmethod
    def crear_solicitud(estudiante_id, periodo_id, materias_ids, observaciones=""):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO solicitudes_inscripcion (estudiante_id, periodo_id, observaciones) "
                    "VALUES (%s,%s,%s) RETURNING id",
                    (estudiante_id, periodo_id, observaciones)
                )
                sol_id = cur.fetchone()["id"]
                for mid in materias_ids:
                    cur.execute(
                        "INSERT INTO solicitud_materias (solicitud_id, materia_id) VALUES (%s,%s)",
                        (sol_id, mid)
                    )
            conn.commit()
            return sol_id

    @staticmethod
    def get_horario(estudiante_id, periodo_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Se cambia 'secciones' por 'cursos' y 'seccion_id' por 'curso_id' en la relación
                cur.execute("""
                    SELECT m.codigo, m.nombre, u.nombre AS docente,
                           c.dia_semana, c.hora_inicio, c.hora_fin, c.aula
                    FROM inscripciones i
                    JOIN cursos c ON c.id = i.curso_id
                    JOIN materias m ON m.id = c.materia_id
                    JOIN usuarios u ON u.id = c.docente_id
                    WHERE i.estudiante_id=%s AND i.periodo_id=%s
                    ORDER BY c.dia_semana, c.hora_inicio
                """, (estudiante_id, periodo_id))
                return cur.fetchall()

    @staticmethod
    def get_notas(estudiante_id, periodo_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Se cambia 'secciones' por 'cursos'
                cur.execute("""
                    SELECT m.codigo, m.nombre,
                           n.p1_nota1, n.p1_nota2, n.p1_nota3,
                           n.p1_peso1, n.p1_peso2, n.p1_peso3,
                           n.p2_nota1, n.p2_nota2, n.p2_nota3,
                           n.p2_peso1, n.p2_peso2, n.p2_peso3,
                           n.examen_final, n.habilitacion,
                           n.nota_definitiva, n.publicado
                    FROM inscripciones i
                    JOIN cursos c ON c.id = i.curso_id
                    JOIN materias m ON m.id = c.materia_id
                    LEFT JOIN notas n ON n.inscripcion_id = i.id
                    WHERE i.estudiante_id=%s AND i.periodo_id=%s
                    ORDER BY m.nombre
                """, (estudiante_id, periodo_id))
                return cur.fetchall()


# ─────────────────────────────────────────────
# DOCENTE
# ─────────────────────────────────────────────
class DocenteModel:
    @staticmethod
    def get_secciones_docente(docente_id, periodo_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Se cambia 'secciones s' por 'cursos c'
                cur.execute("""
                    SELECT c.id, m.codigo, m.nombre AS materia,
                           c.dia_semana, c.hora_inicio, c.hora_fin, c.aula,
                           COUNT(i.id) AS inscritos
                    FROM cursos c
                    JOIN materias m ON m.id = c.materia_id
                    LEFT JOIN inscripciones i ON i.curso_id = c.id
                    WHERE c.docente_id=%s AND c.periodo_id=%s AND c.activa=TRUE
                    GROUP BY c.id, m.codigo, m.nombre, c.dia_semana, c.hora_inicio, c.hora_fin, c.aula
                    ORDER BY m.nombre
                """, (docente_id, periodo_id))
                return cur.fetchall()

    @staticmethod
    def get_inscritos_seccion(curso_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Se cambia 'seccion_id' por 'curso_id'
                cur.execute("""
                    SELECT i.id AS inscripcion_id, u.nombre AS estudiante,
                           u.username, n.p1_nota1, n.p1_nota2, n.p1_nota3,
                           n.p1_peso1, n.p1_peso2, n.p1_peso3,
                           n.p2_nota1, n.p2_nota2, n.p2_nota3,
                           n.p2_peso1, n.p2_peso2, n.p2_peso3,
                           n.examen_final, n.habilitacion,
                           n.nota_definitiva, n.publicado, n.id AS nota_id
                    FROM inscripciones i
                    JOIN usuarios u ON u.id = i.estudiante_id
                    LEFT JOIN notas n ON n.inscripcion_id = i.id
                    WHERE i.curso_id=%s
                    ORDER BY u.nombre
                """, (curso_id,))
                return cur.fetchall()
    
    @staticmethod
    def guardar_notas(inscripcion_id, datos):
        suma_p1 = datos["p1_peso1"] + datos["p1_peso2"] + datos["p1_peso3"]
        suma_p2 = datos["p2_peso1"] + datos["p2_peso2"] + datos["p2_peso3"]

        if round(suma_p1, 2) > 35:
            return False, f"Los pesos del 1er corte suman {suma_p1:.1f}%, no pueden superar 35%"
        if round(suma_p2, 2) > 35:
            return False, f"Los pesos del 2do corte suman {suma_p2:.1f}%, no pueden superar 35%"

        def safe(v):
            try:
                return float(v) if v is not None else 0.0
            except ValueError:
                return 0.0

        def contrib(nota, peso):
            if nota is None:
                return 0.0
            return safe(nota) * safe(peso) / 100.0

        p1 = (contrib(datos["p1_nota1"], datos["p1_peso1"]) +
              contrib(datos["p1_nota2"], datos["p1_peso2"]) +
              contrib(datos["p1_nota3"], datos["p1_peso3"]))

        p2 = (contrib(datos["p2_nota1"], datos["p2_peso1"]) +
              contrib(datos["p2_nota2"], datos["p2_peso2"]) +
              contrib(datos["p2_nota3"], datos["p2_peso3"]))

        # El 3er corte ahora es el Examen Final multiplicado por el 30% completo (0.30)
        p3 = safe(datos["examen_final"]) * 0.30
        definitiva = round(p1 + p2 + p3, 2)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM notas WHERE inscripcion_id=%s", (inscripcion_id,))
                existe = cur.fetchone()

                if existe:
                    cur.execute("""
                        UPDATE notas SET
                            p1_nota1=%s, p1_nota2=%s, p1_nota3=%s,
                            p1_peso1=%s, p1_peso2=%s, p1_peso3=%s,
                            p2_nota1=%s, p2_nota2=%s, p2_nota3=%s,
                            p2_peso1=%s, p2_peso2=%s, p2_peso3=%s,
                            examen_final=%s, nota_definitiva=%s
                        WHERE inscripcion_id=%s
                    """, (
                        datos["p1_nota1"], datos["p1_nota2"], datos["p1_nota3"],
                        datos["p1_peso1"], datos["p1_peso2"], datos["p1_peso3"],
                        datos["p2_nota1"], datos["p2_nota2"], datos["p2_nota3"],
                        datos["p2_peso1"], datos["p2_peso2"], datos["p2_peso3"],
                        datos["examen_final"], definitiva, inscripcion_id
                    ))
                else:
                    cur.execute("""
                        INSERT INTO notas (
                            inscripcion_id,
                            p1_nota1, p1_nota2, p1_nota3,
                            p1_peso1, p1_peso2, p1_peso3,
                            p2_nota1, p2_nota2, p2_nota3,
                            p2_peso1, p2_peso2, p2_peso3,
                            examen_final, nota_definitiva
                        ) VALUES (%s, %s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s,%s, %s,%s)
                    """, (
                        inscripcion_id,
                        datos["p1_nota1"], datos["p1_nota2"], datos["p1_nota3"],
                        datos["p1_peso1"], datos["p1_peso2"], datos["p1_peso3"],
                        datos["p2_nota1"], datos["p2_nota2"], datos["p2_nota3"],
                        datos["p2_peso1"], datos["p2_peso2"], datos["p2_peso3"],
                        datos["examen_final"], definitiva
                    ))
            conn.commit()
        return True, f"Notas actualizadas. Definitiva parcial: {definitiva:.2f}"
            

# ─────────────────────────────────────────────
# ADMINISTRATIVO
# ─────────────────────────────────────────────
class AdminModel:
    @staticmethod
    def get_solicitudes_pendientes(periodo_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT si.id, u.nombre AS estudiante, u.username,
                           si.fecha_solicitud, si.estado, si.observaciones
                    FROM solicitudes_inscripcion si
                    JOIN usuarios u ON u.id = si.estudiante_id
                    WHERE si.periodo_id=%s AND si.estado='pendiente'
                    ORDER BY si.fecha_solicitud
                """, (periodo_id,))
                return cur.fetchall()

    @staticmethod
    def get_materias_solicitud(solicitud_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT m.id, m.codigo, m.nombre
                    FROM solicitud_materias sm
                    JOIN materias m ON m.id = sm.materia_id
                    WHERE sm.solicitud_id=%s
                """, (solicitud_id,))
                return cur.fetchall()

    @staticmethod
    def get_secciones_disponibles(materia_id, periodo_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Se cambia 'secciones s' por 'cursos c' e 'inscripciones.seccion_id' por 'curso_id'
                cur.execute("""
                    SELECT c.id, u.nombre AS docente, c.dia_semana,
                           c.hora_inicio, c.hora_fin, c.aula, c.cupo_max,
                           COUNT(i.id) AS inscritos
                    FROM cursos c
                    JOIN usuarios u ON u.id = c.docente_id
                    LEFT JOIN inscripciones i ON i.curso_id = c.id
                    WHERE c.materia_id=%s AND c.periodo_id=%s AND c.activa=TRUE
                    GROUP BY c.id, u.nombre, c.dia_semana, c.hora_inicio, c.hora_fin, c.aula, c.cupo_max
                    HAVING COUNT(i.id) < c.cupo_max
                """, (materia_id, periodo_id))
                return cur.fetchall()

    @staticmethod
    def asignar_horario(solicitud_id, estudiante_id, periodo_id, asignaciones):
        """
        asignaciones = list of (materia_id, curso_id)
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                for materia_id, curso_id in asignaciones:
                    # Se cambia 'seccion_id' por 'curso_id'
                    cur.execute(
                        "SELECT id FROM inscripciones WHERE estudiante_id=%s AND curso_id=%s AND periodo_id=%s",
                        (estudiante_id, curso_id, periodo_id)
                    )
                    if not cur.fetchone():
                        cur.execute(
                            "INSERT INTO inscripciones (estudiante_id, curso_id, periodo_id) VALUES (%s,%s,%s)",
                            (estudiante_id, curso_id, periodo_id)
                        )
                        # Buscar id del registro recién insertado de forma segura
                        cur.execute(
                            "SELECT id FROM inscripciones WHERE estudiante_id=%s AND curso_id=%s AND periodo_id=%s",
                            (estudiante_id, curso_id, periodo_id)
                        )
                        insc = cur.fetchone()
                        if insc:
                            # Soporte tanto si fetchone devuelve un dict como si devuelve una tupla/objeto
                            insc_id = insc["id"] if isinstance(insc, dict) else insc[0]
                            cur.execute(
                                "INSERT INTO notas (inscripcion_id) VALUES (%s) ON CONFLICT DO NOTHING",
                                (insc_id,)
                            )
                # Marcar solicitud como aprobada
                cur.execute(
                    "UPDATE solicitudes_inscripcion SET estado='aprobada' WHERE id=%s",
                    (solicitud_id,)
                )
            conn.commit()

    @staticmethod
    def rechazar_solicitud(solicitud_id, motivo=""):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE solicitudes_inscripcion SET estado='rechazada', observaciones=%s WHERE id=%s",
                    (motivo, solicitud_id)
                )
            conn.commit()

    @staticmethod
    def get_todos_docentes():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, nombre, email FROM usuarios WHERE rol='docente' AND activo=TRUE ORDER BY nombre"
                )
                return cur.fetchall()

    @staticmethod
    def get_secciones_docente(docente_id, periodo_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Se cambia 'secciones s' por 'cursos c'
                cur.execute("""
                    SELECT c.id, m.codigo, m.nombre AS materia,
                           c.dia_semana, c.hora_inicio, c.hora_fin, c.aula
                    FROM cursos c
                    JOIN materias m ON m.id = c.materia_id
                    WHERE c.docente_id=%s AND c.periodo_id=%s AND c.activa=TRUE
                    ORDER BY m.nombre
                """, (docente_id, periodo_id))
                return cur.fetchall()

    @staticmethod
    def crear_seccion(materia_id, docente_id, periodo_id, dia, hora_inicio, hora_fin, aula, cupo=30):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Se inserta en la tabla 'cursos'
                cur.execute("""
                    INSERT INTO cursos (materia_id, docente_id, periodo_id, dia_semana, hora_inicio, hora_fin, aula, cupo_max)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
                """, (materia_id, docente_id, periodo_id, dia, hora_inicio, hora_fin, aula, cupo))
                res = cur.fetchone()
                new_id = res["id"] if isinstance(res, dict) else res[0]
            conn.commit()
            return new_id

    @staticmethod
    def eliminar_seccion(curso_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Se cambia 'secciones' por 'cursos'
                cur.execute("UPDATE cursos SET activa=FALSE WHERE id=%s", (curso_id,))
            conn.commit()

    @staticmethod
    def registrar_docente(username, nombre, email, password):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (username, password_hash, rol, nombre, email) VALUES (%s,%s,'docente',%s,%s) RETURNING id",
                    (username, hash_password(password), nombre, email)
                )
                res = cur.fetchone()
                new_id = res["id"] if isinstance(res, dict) else res[0]
            conn.commit()
            return new_id

    @staticmethod
    def get_todas_materias():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, codigo, nombre FROM materias WHERE activa=TRUE ORDER BY codigo")
                return cur.fetchall()

    @staticmethod
    def get_periodo_activo():
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, nombre FROM periodos WHERE activo=TRUE LIMIT 1")
                return cur.fetchone()

    @staticmethod
    def get_historial_solicitudes(periodo_id):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT si.id, u.nombre AS estudiante, u.username,
                           si.fecha_solicitud, si.estado
                    FROM solicitudes_inscripcion si
                    JOIN usuarios u ON u.id = si.estudiante_id
                    WHERE si.periodo_id=%s
                    ORDER BY si.estado, si.fecha_solicitud DESC
                """, (periodo_id,))
                return cur.fetchall()