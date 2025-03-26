from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import pandas as pd
from datetime import datetime, timedelta
from config import conectar_db
from prediccion_servicio import ServicioPrediccion

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializar el servicio de predicción
servicio = ServicioPrediccion("modelos/prediccion")

@app.route('/')
def index():
    """Página principal con resumen de predicciones."""
    # Obtener predicciones de valor para los próximos días
    predicciones = servicio.predecir_proximos_partidos(dias=7, min_valor=0.05, min_confianza=0.1)
    
    # Obtener estadísticas del modelo
    stats = servicio.obtener_stats_modelo(dias=60)
    
    # Obtener próximos partidos
    conn = conectar_db()
    proximos_partidos = []
    
    if conn:
        cursor = conn.cursor()
        
        try:
            fecha_limite = datetime.now() + timedelta(days=7)
            
            cursor.execute("""
                SELECT 
                    p.id,
                    e1.nombre AS local,
                    e2.nombre AS visitante,
                    l.nombre AS liga,
                    p.fecha
                FROM partidos p
                JOIN equipos e1 ON p.equipo_local_id = e1.id
                JOIN equipos e2 ON p.equipo_visitante_id = e2.id
                JOIN ligas l ON p.liga_id = l.id
                WHERE p.fecha BETWEEN NOW() AND %s
                  AND p.terminado = FALSE
                ORDER BY p.fecha ASC
            """, (fecha_limite,))
            
            for row in cursor.fetchall():
                proximos_partidos.append({
                    'id': row[0],
                    'local': row[1],
                    'visitante': row[2],
                    'liga': row[3],
                    'fecha': row[4]
                })
                
        except Exception as e:
            print(f"Error al obtener próximos partidos: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template(
        'index.html',
        predicciones=predicciones,
        stats=stats,
        proximos_partidos=proximos_partidos
    )

@app.route('/prediccion/<int:partido_id>')
def ver_prediccion(partido_id):
    """Muestra la predicción detallada para un partido específico."""
    prediccion = servicio.predecir_partido(partido_id)
    
    if "error" in prediccion:
        return render_template('error.html', mensaje=prediccion["error"])
    
    return render_template('prediccion.html', prediccion=prediccion)

@app.route('/partidos')
def listar_partidos():
    """Lista todos los partidos próximos."""
    dias = request.args.get('dias', 7, type=int)
    liga = request.args.get('liga', None)
    
    conn = conectar_db()
    partidos = []
    ligas = []
    
    if conn:
        cursor = conn.cursor()
        
        try:
            # Obtener lista de ligas
            cursor.execute("SELECT id, nombre FROM ligas ORDER BY nombre")
            ligas = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
            
            # Construir consulta con filtros
            query = """
                SELECT 
                    p.id,
                    e1.nombre AS local,
                    e2.nombre AS visitante,
                    l.nombre AS liga,
                    p.fecha,
                    c1.valor AS cuota_local,
                    c2.valor AS cuota_empate,
                    c3.valor AS cuota_visitante
                FROM partidos p
                JOIN equipos e1 ON p.equipo_local_id = e1.id
                JOIN equipos e2 ON p.equipo_visitante_id = e2.id
                JOIN ligas l ON p.liga_id = l.id
                LEFT JOIN cuotas c1 ON c1.partido_id = p.id AND c1.tipo_apuesta = 'Local'
                LEFT JOIN cuotas c2 ON c2.partido_id = p.id AND c2.tipo_apuesta = 'Empate'
                LEFT JOIN cuotas c3 ON c3.partido_id = p.id AND c3.tipo_apuesta = 'Visitante'
                WHERE p.fecha BETWEEN NOW() AND NOW() + INTERVAL %s DAY
                  AND p.terminado = FALSE
            """
            
            params = [dias]
            
            if liga:
                query += " AND l.id = %s"
                params.append(liga)
                
            query += " ORDER BY p.fecha ASC"
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                partidos.append({
                    'id': row[0],
                    'local': row[1],
                    'visitante': row[2],
                    'liga': row[3],
                    'fecha': row[4],
                    'cuota_local': row[5],
                    'cuota_empate': row[6],
                    'cuota_visitante': row[7]
                })
                
        except Exception as e:
            print(f"Error al listar partidos: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template(
        'partidos.html',
        partidos=partidos,
        ligas=ligas,
        dias_seleccionados=dias,
        liga_seleccionada=liga
    )

@app.route('/historial')
def historial_predicciones():
    """Muestra el historial de predicciones y su precisión."""
    conn = conectar_db()
    predicciones = []
    
    if conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    pred.id,
                    e1.nombre AS local,
                    e2.nombre AS visitante,
                    l.nombre AS liga,
                    p.fecha,
                    p.goles_local,
                    p.goles_visitante,
                    pred.resultado_predicho,
                    pred.prob_local,
                    pred.prob_empate,
                    pred.prob_visitante,
                    pred.acertada,
                    pred.fecha_prediccion
                FROM predicciones pred
                JOIN partidos p ON pred.partido_id = p.id
                JOIN equipos e1 ON p.equipo_local_id = e1.id
                JOIN equipos e2 ON p.equipo_visitante_id = e2.id
                JOIN ligas l ON p.liga_id = l.id
                ORDER BY p.fecha DESC
                LIMIT 100
            """)
            
            for row in cursor.fetchall():
                # Convertir resultado numérico a texto
                resultado_texto = "Victoria Local"
                if row[7] == 1:
                    resultado_texto = "Empate"
                elif row[7] == 2:
                    resultado_texto = "Victoria Visitante"
                
                predicciones.append({
                    'id': row[0],
                    'local': row[1],
                    'visitante': row[2],
                    'liga': row[3],
                    'fecha_partido': row[4],
                    'goles_local': row[5],
                    'goles_visitante': row[6],
                    'resultado_predicho': resultado_texto,
                    'prob_local': row[8],
                    'prob_empate': row[9],
                    'prob_visitante': row[10],
                    'acertada': row[11],
                    'fecha_prediccion': row[12]
                })
                
        except Exception as e:
            print(f"Error al obtener historial: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('historial.html', predicciones=predicciones)

@app.route('/api/actualizar-datos', methods=['POST'])
def actualizar_datos():
    """Endpoint para actualizar datos y entrenar modelo."""
    try:
        from extraccion_datos import obtener_partidos_proximos, extraer_estadisticas_historicas
        
        # Extraer datos
        dias = request.form.get('dias', 7, type=int)
        partidos = obtener_partidos_proximos(dias=dias)
        extraer_estadisticas_historicas()
        
        # Actualizar predicciones pasadas
        servicio.actualizar_predicciones_pasadas()
        
        return jsonify({'success': True, 'message': f'Datos actualizados. {len(partidos)} partidos extraídos.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/entrenar-modelo', methods=['POST'])
def entrenar_modelo():
    """Endpoint para entrenar el modelo."""
    try:
        # Entrenar modelo
        resultado = servicio.modelo.entrenar_modelo("modelos/prediccion")
        mensaje = "Modelo entrenado correctamente" if resultado else "Error al entrenar el modelo"
        
        return jsonify({'success': resultado, 'message': mensaje})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)