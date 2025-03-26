import psycopg2

def conectar_db():
    """Establece conexión con PostgreSQL y la devuelve."""
    try:
        conn = psycopg2.connect(
            dbname="apuestas",
            user="proyect",
            password="Futbol123",  # Mantuve la misma contraseña, cámbiala si es necesario
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con PostgreSQL: {e}")
        return None