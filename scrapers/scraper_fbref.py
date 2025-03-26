import requests
from bs4 import BeautifulSoup
from config import conectar_db


def obtener_estadisticas():
    """Extrae estadísticas de jugadores desde FBRef y las almacena en la base de datos."""
    url = "https://fbref.com/en/players/f6c57f0c/Wisdom-Mike"

    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print(
            f"❌ Error al obtener datos de FBRef. Código {
                response.status_code}"
        )
        return

    soup = BeautifulSoup(response.text, "html.parser")

    nombre_elemento = soup.find("h1")
    if not nombre_elemento:
        print("⚠️ No se encontró el nombre del jugador en la página.")
        return

    nombre_jugador = nombre_elemento.text.strip()
    print(f"📌 Jugador encontrado: {nombre_jugador}")

    conn = conectar_db()
    if not conn:
        return

    cursor = conn.cursor()

    # Obtener ID del jugador
    cursor.execute("SELECT id FROM jugadores WHERE nombre = %s", (nombre_jugador,))
    jugador = cursor.fetchone()

    if jugador:
        jugador_id = jugador[0]
    else:
        cursor.execute(
            "INSERT INTO jugadores (nombre) VALUES (%s) RETURNING id", (nombre_jugador,)
        )
        jugador = cursor.fetchone()
        if jugador:
            jugador_id = jugador[0]
        else:
            print("⚠️ No se pudo obtener el ID del jugador tras la inserción.")
            conn.rollback()
            cursor.close()
            conn.close()
            return

    print(f"✅ ID del jugador obtenido: {jugador_id}")

    # Obtener estadísticas
    stats = soup.find("table", {"id": "stats_standard"})
    if stats:
        filas = stats.find("tbody").find_all("tr")
        ultima_fila = filas[-1] if filas else None

        def obtener_valor(celda):
            return celda.text.strip() if celda else "0"

        if ultima_fila:
            minutos = obtener_valor(ultima_fila.find("td", {"data-stat": "minutes"}))
            goles = obtener_valor(ultima_fila.find("td", {"data-stat": "goals"}))
            asistencias = obtener_valor(
                ultima_fila.find("td", {"data-stat": "assists"})
            )
            tiros = obtener_valor(ultima_fila.find("td", {"data-stat": "shots_total"}))
            tiros_a_puerta = obtener_valor(
                ultima_fila.find("td", {"data-stat": "shots_on_target"})
            )
            tarjetas_amarillas = obtener_valor(
                ultima_fila.find("td", {"data-stat": "cards_yellow"})
            )
            tarjetas_rojas = obtener_valor(
                ultima_fila.find("td", {"data-stat": "cards_red"})
            )

            cursor.execute(
                """
                INSERT INTO estadisticas_jugadores (jugador_id, minutos_jugados, goles, asistencias, tiros, tiros_a_puerta, tarjetas_amarillas, tarjetas_rojas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (jugador_id) DO UPDATE
                SET minutos_jugados = EXCLUDED.minutos_jugados, goles = EXCLUDED.goles, asistencias = EXCLUDED.asistencias,
                    tiros = EXCLUDED.tiros, tiros_a_puerta = EXCLUDED.tiros_a_puerta,
                    tarjetas_amarillas = EXCLUDED.tarjetas_amarillas, tarjetas_rojas = EXCLUDED.tarjetas_rojas;
            """,
                (
                    jugador_id,
                    minutos,
                    goles,
                    asistencias,
                    tiros,
                    tiros_a_puerta,
                    tarjetas_amarillas,
                    tarjetas_rojas,
                ),
            )

            conn.commit()
            print("✅ Estadísticas insertadas en PostgreSQL.")

    cursor.close()
    conn.close()
