from config import conectar_db

def crear_tablas_basicas():
    """Crea las tablas básicas necesarias para la aplicación."""
    conn = conectar_db()
    if not conn:
        print("No se pudo conectar a la base de datos")
        return

    cursor = conn.cursor()
    
    # Tabla de ligas
    cursor.execute("""
        DROP TABLE IF EXISTS ligas CASCADE;
        CREATE TABLE ligas (
            id SERIAL PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL,
            pais TEXT NOT NULL,
            url TEXT NOT NULL
        );
    """)

    # Tabla de equipos
    cursor.execute("""
        DROP TABLE IF EXISTS equipos CASCADE;
        CREATE TABLE equipos (
            id SERIAL PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL,
            liga_id INTEGER REFERENCES ligas(id) ON DELETE CASCADE,
            url TEXT
        );
    """)

    # Tabla de partidos
    cursor.execute("""
        DROP TABLE IF EXISTS partidos CASCADE;
        CREATE TABLE partidos (
            id SERIAL PRIMARY KEY,
            equipo_local INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            equipo_visitante INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            fecha TIMESTAMP NOT NULL,
            goles_local INTEGER,
            goles_visitante INTEGER,
            terminado BOOLEAN DEFAULT FALSE,
            UNIQUE (equipo_local, equipo_visitante, fecha)
        );
    """)

    # Datos de ejemplo
    cursor.execute("INSERT INTO ligas (nombre, pais, url) VALUES ('LaLiga', 'España', 'https://example.com/laliga');")
    cursor.execute("INSERT INTO ligas (nombre, pais, url) VALUES ('Premier League', 'Inglaterra', 'https://example.com/premier');")
    
    cursor.execute("INSERT INTO equipos (nombre, liga_id, url) VALUES ('Barcelona', 1, 'https://example.com/barcelona');")
    cursor.execute("INSERT INTO equipos (nombre, liga_id, url) VALUES ('Real Madrid', 1, 'https://example.com/realmadrid');")
    cursor.execute("INSERT INTO equipos (nombre, liga_id, url) VALUES ('Manchester United', 2, 'https://example.com/manutd');")
    cursor.execute("INSERT INTO equipos (nombre, liga_id, url) VALUES ('Liverpool', 2, 'https://example.com/liverpool');")
    
    # Partidos de ejemplo
    cursor.execute("""
        INSERT INTO partidos (equipo_local, equipo_visitante, fecha) 
        VALUES (1, 2, NOW() + INTERVAL '2 days');
    """)
    cursor.execute("""
        INSERT INTO partidos (equipo_local, equipo_visitante, fecha) 
        VALUES (3, 4, NOW() + INTERVAL '3 days');
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tablas básicas creadas y datos de ejemplo insertados")

if __name__ == "__main__":
    crear_tablas_basicas()