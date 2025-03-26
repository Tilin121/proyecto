from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import pandas as pd
from datetime import datetime, timedelta
from config import conectar_db

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route("/")
def index():
    """Página principal con resumen."""
    # Simulamos datos para la vista
    predicciones = []
    stats = {
        "total_predicciones": 0,
        "acertadas": 0,
        "tasa_acierto": 0,
        "retorno_inversion": 0,
    }

    proximos_partidos = []

    conn = conectar_db()
    if conn:
        cursor = conn.cursor()
        try:
            fecha_limite = datetime.now() + timedelta(days=7)

            cursor.execute(
                """
                SELECT
                    p.id,
                    e1.nombre AS local,
                    e2.nombre AS visitante,
                    l.nombre AS liga,
                    p.fecha
                FROM partidos p
                JOIN equipos e1 ON p.equipo_local = e1.id
                JOIN equipos e2 ON p.equipo_visitante = e2.id
                JOIN ligas l ON e1.liga_id = l.id
                WHERE p.fecha BETWEEN NOW() AND %s
                  AND p.terminado = FALSE
                ORDER BY p.fecha ASC
                LIMIT 5
            """,
                (fecha_limite,),
            )

            for row in cursor.fetchall():
                proximos_partidos.append(
                    {
                        "id": row[0],
                        "local": row[1],
                        "visitante": row[2],
                        "liga": row[3],
                        "fecha": row[4],
                    }
                )

        except Exception as e:
            print(f"Error al obtener próximos partidos: {e}")
        finally:
            cursor.close()
            conn.close()

    return render_template(
        "index.html",
        predicciones=predicciones,
        stats=stats,
        proximos_partidos=proximos_partidos,
    )


@app.route("/partidos")
def listar_partidos():
    """Lista todos los partidos próximos."""
    dias = request.args.get("dias", 7, type=int)
    liga = request.args.get("liga", None)

    conn = conectar_db()
    partidos = []
    ligas = []

    if conn:
        cursor = conn.cursor()

        try:
            # Obtener lista de ligas
            cursor.execute("SELECT id, nombre FROM ligas ORDER BY nombre")
            ligas = [{"id": row[0], "nombre": row[1]} for row in cursor.fetchall()]

            # Construir consulta con filtros
            query = """
    SELECT
        p.id,
        e1.nombre AS local,
        e2.nombre AS visitante,
        l.nombre AS liga,
        p.fecha
    FROM partidos p
    JOIN equipos e1 ON p.equipo_local = e1.id
    JOIN equipos e2 ON p.equipo_visitante = e2.id
    JOIN ligas l ON e1.liga_id = l.id
    WHERE p.fecha BETWEEN NOW() AND NOW() + INTERVAL %s DAY
"""

            params = [dias]

            if liga:
                query += " AND l.id = %s"
                params.append(liga)

            query += " ORDER BY p.fecha ASC"

            cursor.execute(query, params)

            for row in cursor.fetchall():
                partidos.append(
                    {
                        "id": row[0],
                        "local": row[1],
                        "visitante": row[2],
                        "liga": row[3],
                        "fecha": row[4],
                        "cuota_local": 2.0,
                        "cuota_empate": 3.0,
                        "cuota_visitante": 3.5,
                    }
                )

        except Exception as e:
            print(f"Error al listar partidos: {e}")
        finally:
            cursor.close()
            conn.close()

    return render_template(
        "partidos.html",
        partidos=partidos,
        ligas=ligas,
        dias_seleccionados=dias,
        liga_seleccionada=liga,
    )


@app.route("/api/actualizar-datos", methods=["POST"])
def actualizar_datos():
    """Endpoint para actualizar datos."""
    return jsonify({"success": True, "message": "Datos actualizados (simulación)."})


@app.route("/api/entrenar-modelo", methods=["POST"])
def entrenar_modelo():
    """Endpoint para entrenar el modelo."""
    return jsonify({"success": True, "message": "Modelo entrenado (simulación)."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
