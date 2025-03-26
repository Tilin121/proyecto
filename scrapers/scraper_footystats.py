import requests
from bs4 import BeautifulSoup
from database import conectar_db

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

URL_BASE = "https://footystats.org"


def limpiar_nombre_equipo(nombre):
    """Limpia el nombre del equipo eliminando datos extra."""
    return nombre.split("UEFA")[0].split("Premier League")[0].split("Forma")[0].strip()


def obtener_ligas():
    """Extrae las ligas de FootyStats y las almacena en la base de datos."""
    print("\n🔹 Obteniendo ligas de FootyStats...")
    response = requests.get(f"{URL_BASE}/es/", headers=HEADERS)

    if response.status_code != 200:
        print(
            f"❌ Error al obtener datos de FootyStats. Código {
                response.status_code}"
        )
        return {}

    soup = BeautifulSoup(response.text, "html.parser")
    ligas = {}

    for liga in soup.find_all("a", href=True):
        if "/es/" in liga["href"] and "league" in liga["href"]:
            nombre = liga.text.strip()
            enlace = liga["href"]

            if not enlace.startswith("https://"):
                enlace = URL_BASE + enlace

            if nombre and enlace:
                ligas[nombre] = enlace

    print(f"✅ {len(ligas)} ligas encontradas.")

    conn = conectar_db()
    if not conn:
        return ligas

    cursor = conn.cursor()
    for nombre, url in ligas.items():
        cursor.execute(
            """
            INSERT INTO ligas (nombre, url)
            VALUES (%s, %s)
            ON CONFLICT (nombre) DO NOTHING;
        """,
            (nombre, url),
        )

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Ligas almacenadas en la base de datos.")
    return ligas


def obtener_equipos_y_cuotas(url_liga, nombre_liga):
    """Extrae los equipos y cuotas de una liga en FootyStats."""
    print(f"\n📌 Obteniendo equipos y cuotas de {nombre_liga}...")

    response = requests.get(url_liga, headers=HEADERS)
    if response.status_code != 200:
        print(
            f"❌ Error al obtener equipos de {nombre_liga}. Código {
                response.status_code}"
        )
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    equipos = {}
    cuotas = []

    # 📌 Extraer equipos
    for link in soup.select("a"):
        href = link.get("href", "")
        if "/es/clubs/" in href:
            nombre_equipo = limpiar_nombre_equipo(link.text.strip())
            if nombre_equipo and not nombre_equipo.isdigit():
                equipos[nombre_equipo] = (
                    URL_BASE + href if not href.startswith("https") else href
                )

    # 📌 Extraer cuotas de partidos
    for partido in soup.select("div.match-odds-container"):
        equipos_partido = partido.select("span.team-name")
        cuotas_partido = partido.select("span.odds-value")

        if len(equipos_partido) == 2 and len(cuotas_partido) >= 3:
            equipo_local = equipos_partido[0].text.strip()
            equipo_visitante = equipos_partido[1].text.strip()
            cuota_local = cuotas_partido[0].text.strip()
            cuota_empate = cuotas_partido[1].text.strip()
            cuota_visitante = cuotas_partido[2].text.strip()
            casa_apuestas = (
                "FootyStats"  # Se puede mejorar si hay varias casas de apuestas
            )

            # 📌 Validar que las cuotas sean numéricas
            if (
                cuota_local.replace(".", "").isdigit()
                and cuota_empate.replace(".", "").isdigit()
                and cuota_visitante.replace(".", "").isdigit()
            ):
                cuotas.append(
                    (equipo_local, "Victoria Local", float(cuota_local), casa_apuestas)
                )
                cuotas.append(
                    (
                        equipo_visitante,
                        "Victoria Visitante",
                        float(cuota_visitante),
                        casa_apuestas,
                    )
                )
                cuotas.append(("Empate", "Empate", float(cuota_empate), casa_apuestas))

    print(
        f"✅ {
            len(equipos)} equipos y {
            len(cuotas)} cuotas extraídas de {nombre_liga}."
    )

    # Guardar en la base de datos
    conn = conectar_db()
    if not conn:
        return equipos

    cursor = conn.cursor()

    # 📌 Insertar equipos
    for nombre, url in equipos.items():
        try:
            cursor.execute(
                """
                INSERT INTO equipos (nombre, liga_id, url)
                VALUES (%s, (SELECT id FROM ligas WHERE nombre = %s), %s)
                ON CONFLICT (nombre) DO NOTHING;
            """,
                (nombre, nombre_liga, url),
            )
        except Exception as e:
            print(f"❌ Error al insertar equipo {nombre}: {e}")

    # 📌 Insertar cuotas
    for equipo, tipo, valor, casa in cuotas:
        try:
            cursor.execute("SELECT id FROM equipos WHERE nombre = %s", (equipo,))
            equipo_id = cursor.fetchone()

            if equipo_id:
                equipo_id = equipo_id[0]
                cursor.execute(
                    """
                    INSERT INTO cuotas (equipo_id, tipo_apuesta, valor, casa_apuestas, fecha)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (equipo_id, tipo_apuesta, casa_apuestas) DO UPDATE
                    SET valor = EXCLUDED.valor, fecha = NOW();
                """,
                    (equipo_id, tipo, valor, casa),
                )
            else:
                print(
                    f"⚠️ Equipo '{equipo}' no encontrado en la BD. No se insertó la cuota."
                )

        except Exception as e:
            print(f"❌ Error al insertar cuota de {equipo}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Equipos y cuotas de {nombre_liga} almacenados en la base de datos.")
    return equipos
