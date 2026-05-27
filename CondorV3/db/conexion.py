import psycopg2
from psycopg2.extras import RealDictCursor

#Clase encargada de conectarse a la base de datos
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "Nombre de la base de datos", #En database especificar la bd creada
    "user": "Su usuario", #usuario 
    "password": "Su contraseña" #contraseña propia
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def test_connection():
    try:
        conn = get_connection()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)
