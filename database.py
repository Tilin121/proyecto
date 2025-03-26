from config import conectar_db

def crear_tablas():
    """Crea las tablas necesarias en PostgreSQL si no existen."""
    conn = conectar_db()
    if not conn:
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

    # Tabla de jugadores
    cursor.execute("""
        DROP TABLE IF EXISTS jugadores CASCADE;
        CREATE TABLE jugadores (
            id SERIAL PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            posicion TEXT,
            nacionalidad TEXT,
            edad INTEGER
        );
    """)

    # Tabla de estadísticas de jugadores
    cursor.execute("""
        DROP TABLE IF EXISTS estadisticas_jugadores CASCADE;
        CREATE TABLE estadisticas_jugadores (
            id SERIAL PRIMARY KEY,
            jugador_id INTEGER REFERENCES jugadores(id) ON DELETE CASCADE,
            minutos_jugados INTEGER DEFAULT 0,
            goles INTEGER DEFAULT 0,
            asistencias INTEGER DEFAULT 0,
            tiros INTEGER DEFAULT 0,
            tiros_a_puerta INTEGER DEFAULT 0,
            tarjetas_amarillas INTEGER DEFAULT 0,
            tarjetas_rojas INTEGER DEFAULT 0,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            UNIQUE (jugador_id)
        );
    """)

    # Tabla de partidos
    cursor.execute("""
        DROP TABLE IF EXISTS partidos CASCADE;
        CREATE TABLE partidos (
            id SERIAL PRIMARY KEY,
            equipo_local_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            equipo_visitante_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            liga_id INTEGER REFERENCES ligas(id) ON DELETE CASCADE,
            fecha TIMESTAMP NOT NULL,
            goles_local INTEGER,
            goles_visitante INTEGER,
            terminado BOOLEAN DEFAULT FALSE,
            UNIQUE (equipo_local_id, equipo_visitante_id, fecha)
        );
    """)

    # Tabla de cuotas
    cursor.execute("""
        DROP TABLE IF EXISTS cuotas CASCADE;
        CREATE TABLE cuotas (
            id SERIAL PRIMARY KEY,
            partido_id INTEGER REFERENCES partidos(id) ON DELETE CASCADE,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            tipo_apuesta TEXT NOT NULL, -- 'Local', 'Visitante', 'Empate', etc.
            valor NUMERIC(7,2) NOT NULL,
            casa_apuestas TEXT NOT NULL,
            fecha TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (partido_id, tipo_apuesta, casa_apuestas)
        );
    """)

    # Tabla de estadísticas históricas de equipos
    cursor.execute("""
        DROP TABLE IF EXISTS estadisticas_historicas CASCADE;
        CREATE TABLE estadisticas_historicas (
            id SERIAL PRIMARY KEY,
            equipo_id INTEGER REFERENCES equipos(id) ON DELETE CASCADE,
            fecha DATE NOT NULL,
            es_local BOOLEAN NOT NULL,
            goles_favor INTEGER NOT NULL,
            goles_contra INTEGER NOT NULL,
            posesion INTEGER,
            xg NUMERIC(5,2), -- Expected goals
            xga NUMERIC(5,2), -- Expected goals against
            UNIQUE (equipo_id, fecha)
        );
    """)

    # Tabla de predicciones
    cursor.execute("""
        DROP TABLE IF EXISTS predicciones CASCADE;
        CREATE TABLE predicciones (
            id SERIAL PRIMARY KEY,
            partido_id INTEGER REFERENCES partidos(id) ON DELETE CASCADE,
            fecha_prediccion TIMESTAMP NOT NULL DEFAULT NOW(),
            prob_local NUMERIC(5,2) NOT NULL,
            prob_empate NUMERIC(5,2) NOT NULL,
            prob_visitante NUMERIC(5,2) NOT NULL,
            resultado_predicho INTEGER NOT NULL, -- 0: local, 1: empate, 2: visitante
            valor_local NUMERIC(5,2), -- Valor esperado (prob * cuota - 1)
            valor_empate NUMERIC(5,2),
            valor_visitante NUMERIC(5,2),
            confianza NUMERIC(5,2), -- Nivel de confianza de la predicción (0-1)
            acertada BOOLEAN, -- NULL si no ha terminado, TRUE/FALSE después
            UNIQUE (partido_id, fecha_prediccion)
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tablas creadas correctamente")