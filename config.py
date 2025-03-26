import psycopg2


def conectar_db():
    """Establece conexión con PostgreSQL y la devuelve."""
    try:
        conn = psycopg2.connect(
            dbname="proyect",
            user="postgres",
            password="Futbol123",  # Asegúrate de que esta sea la contraseña correcta
            host="localhost",
            port="5432",
        )
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con PostgreSQL: {e}")
        return None
