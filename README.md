# Sistema de Gestión Académica

Sistema local desarrollado en Python + PostgreSQL con interfaz gráfica Tkinter.

## Requisitos

- Python 3.9+
- PostgreSQL 13+
- psycopg2-binary

## Instalación

```bash
pip install psycopg2-binary
```

## Configuración de PostgreSQL

Edita `db/connection.py` si tus credenciales de Postgres son diferentes:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "Nombre de la base de datos",
    "user": "Su usario",
    "password": "Su contraseña"   
}
```

## Inicialización

Iniciar el entorno de python env *en la raiz del proyecto* 
```bash
python -m venv venv
source venv/bin/activate
``` 

En la base hay:
- 20 estudiantes (`est01`–`est20`)
- 12 docentes (`doc01`–`doc12`)
- 3 administrativos (`admin01`–`admin03`)
- 12 materias
- 1 periodo activo: **2024-2**

**Contraseña de todos los usuarios: `123456`**

Para volcar la bd:

```bash
psql -h localhost -U tu_usuario_postgres -d condor_db -f Postgrest.txt
```

## Ejecución

```bash
python main.py
```

---

## Flujo de uso

### Estudiante
1. Login con `est01` / `123456`
2. **Inscripción**: selecciona materias → envía solicitud
3. **Mi Horario**: ver horario (disponible tras aprobación)
4. **Mis Notas**: ver notas publicadas por el docente

### Administrativo
1. Login con `admin01` / `123456`
2. **Solicitudes**: ver pendientes → seleccionar sección por materia → aprobar o rechazar
3. **Horarios Docentes**: crear/eliminar secciones para cada docente
4. **Registrar Docente**: inscribir nuevos profesores
5. **Historial**: ver todas las solicitudes

### Docente
1. Login con `doc01` / `123456`
2. **Mis Cursos**: ver secciones asignadas y lista de inscritos
3. **Ingresar Notas**:
   - Selecciona sección
   - Por cada estudiante llena notas y pesos
   - **1er corte**: 3 notas con sus pesos (suma pesos ≤ 35%, cada uno ≤ 30%)
   - **2do corte**: igual que el 1er corte
   - **3er corte**: Examen final (×20%) + Habilitación (×10%) = 30% fijo
   - Notas entre 0 y 50
   - Guarda individual → publica sección completa

---

## Estructura del proyecto

```
academia/
├── main.py                  # Punto de entrada
├── db/
│   ├── connection.py        # Configuración DB
│   └── setup.py             # Crear tablas y seed
├── models/
│   └── models.py            # Capa de datos (SQL)
└── views/
    ├── base_view.py         # Ventana base + constantes UI
    ├── login_view.py        # Login
    ├── estudiante_view.py   # Portal estudiante
    ├── docente_view.py      # Portal docente
    └── admin_view.py        # Portal administrativo
```

## Cálculo de nota definitiva

```
Definitiva = (Σ nota_i × peso_i / 100) [1er corte]
           + (Σ nota_i × peso_i / 100) [2do corte]
           + examen_final × 0.20 + habilitacion × 0.10
```

Ejemplo: 
- 1er corte: nota 40 peso 20%, nota 35 peso 15% → subtotal = 8 + 5.25 = 13.25
- 2do corte: nota 45 peso 35% → subtotal = 15.75
- Examen: 42 → 42×0.20 = 8.4 | Habilitación: 0 → 0
- **Definitiva: 13.25 + 15.75 + 8.4 = 37.4 / 100**
  
