import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import conectar_db
from modelo_prediccion import ModeloPrediccion

class ServicioPrediccion:
    def __init__(self, ruta_modelo=None):
        """Inicializa el servicio de predicción."""
        self.modelo = ModeloPrediccion(ruta_modelo)
        
    def _obtener_estadisticas_equipo(self, equipo_id, es_local=True, partidos=5):
        """
        Obtiene estadísticas históricas de un equipo para los últimos N partidos.
        """
        conn = conectar_db()
        if not conn:
            return {}
            
        cursor = conn.cursor()
        
        try:
            # Simulamos estadísticas básicas para el equipo
            return {
                "goles_favor_media": 1.5,
                "goles_contra_media": 0.8,
                "posesion_media": 55,
                "xg_media": 1.7,
                "xga_media": 0.9,
                "victorias": 3,
                "empates": 1,
                "derrotas": 1,
                "tendencia_goles": 0.2,
                "goles_favor_condicion": 1.8 if es_local else 1.2,
                "goles_contra_condicion": 0.6 if es_local else 1.1
            }
            
        except Exception as e:
            print(f"❌ Error al obtener estadísticas de equipo {equipo_id}: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()
    
    def preparar_datos_partido(self, partido_id):
        """
        Prepara los datos de un partido para la predicción.
        """
        conn = conectar_db()
        if not conn:
            return None, None
            
        cursor = conn.cursor()
        
        try:
            # Obtener información del partido
            cursor.execute("""
                SELECT 
                    p.id,
                    e1.id AS equipo_local_id, 
                    e1.nombre AS equipo_local,
                    e2.id AS equipo_visitante_id, 
                    e2.nombre AS equipo_visitante,
                    l.nombre AS liga,
                    p.fecha
                FROM partidos p
                JOIN equipos e1 ON p.equipo_local = e1.id
                JOIN equipos e2 ON p.equipo_visitante = e2.id
                JOIN ligas l ON e1.liga_id = l.id
                WHERE p.id = %s
            """, (partido_id,))
            
            partido = cursor.fetchone()
            
            if not partido:
                print(f"❌ No se encontró el partido con ID {partido_id}")
                return None, None
                
            partido_id, local_id, local_nombre, visitante_id, visitante_nombre, liga, fecha = partido
            
            # Simulamos cuotas
            cuotas = {"Local": 2.0, "Empate": 3.0, "Visitante": 3.5}
            
            # Obtener estadísticas de los equipos
            stats_local = self._obtener_estadisticas_equipo(local_id, es_local=True)
            stats_visitante = self._obtener_estadisticas_equipo(visitante_id, es_local=False)
            
            # Preparar datos para el modelo
            datos = {
                # Estadísticas del equipo local
                "goles_favor_local": stats_local.get("goles_favor_media", 0),
                "goles_contra_local": stats_local.get("goles_contra_media", 0),
                "posesion_local": stats_local.get("posesion_media", 50),
                "xg_local": stats_local.get("xg_media", 1.0),
                "xga_local": stats_local.get("xga_media", 1.0),
                "victorias_local": stats_local.get("victorias", 0),
                "empates_local": stats_local.get("empates", 0),
                "derrotas_local": stats_local.get("derrotas", 0),
                "tendencia_local": stats_local.get("tendencia_goles", 0),
                
                # Estadísticas del equipo visitante
                "goles_favor_visitante": stats_visitante.get("goles_favor_media", 0),
                "goles_contra_visitante": stats_visitante.get("goles_contra_media", 0),
                "posesion_visitante": stats_visitante.get("posesion_media", 50),
                "xg_visitante": stats_visitante.get("xg_media", 1.0),
                "xga_visitante": stats_visitante.get("xga_media", 1.0),
                "victorias_visitante": stats_visitante.get("victorias", 0),
                "empates_visitante": stats_visitante.get("empates", 0),
                "derrotas_visitante": stats_visitante.get("derrotas", 0),
                "tendencia_visitante": stats_visitante.get("tendencia_goles", 0),
                
                # Cuotas
                "cuota_local": cuotas["Local"],
                "cuota_empate": cuotas["Empate"],
                "cuota_visitante": cuotas["Visitante"],
            }
            
            # Información adicional para mostrar
            info_partido = {
                "id": partido_id,
                "local": local_nombre,
                "visitante": visitante_nombre,
                "liga": liga,
                "fecha": fecha,
                "cuotas": cuotas
            }
            
            return pd.DataFrame([datos]), info_partido
            
        except Exception as e:
            print(f"❌ Error al preparar datos del partido {partido_id}: {e}")
            return None, None
        finally:
            cursor.close()
            conn.close()
    
    def predecir_partido(self, partido_id):
        """
        Realiza la predicción para un partido específico.
        """
        # Preparar datos
        datos, info = self.preparar_datos_partido(partido_id)
        
        if datos is None or info is None:
            return {"error": "No se pudieron obtener los datos del partido"}
        
        # Realizar predicción
        try:
            # Simulamos el resultado del modelo con valores fijos
            resultado = 0  # Victoria local
            probabilidades = [0.6, 0.2, 0.2]  # [local, empate, visitante]
            
            # Evaluar valor de las apuestas
            cuotas = [
                info["cuotas"]["Local"],
                info["cuotas"]["Empate"],
                info["cuotas"]["Visitante"]
            ]
            
            valor_apuestas = [prob * cuota - 1 for prob, cuota in zip(probabilidades, cuotas)]
            
            # Determinar apuesta recomendada
            mejor_valor_idx = np.argmax(valor_apuestas)
            mejor_valor = valor_apuestas[mejor_valor_idx]
            
            resultados = ["Victoria Local", "Empate", "Victoria Visitante"]
            
            # Confianza (diferencia entre la mayor probabilidad y la siguiente)
            probs_ordenadas = sorted(probabilidades, reverse=True)
            confianza = probs_ordenadas[0] - probs_ordenadas[1]
            
            return {
                "partido": info,
                "prediccion": {
                    "resultado_predicho": resultado,
                    "resultado_nombre": resultados[resultado],
                    "probabilidades": {
                        "local": probabilidades[0],
                        "empate": probabilidades[1],
                        "visitante": probabilidades[2]
                    },
                    "valor_apuestas": {
                        "local": valor_apuestas[0],
                        "empate": valor_apuestas[1],
                        "visitante": valor_apuestas[2]
                    },
                    "apuesta_recomendada": resultados[mejor_valor_idx],
                    "valor_esperado": mejor_valor,
                    "confianza": confianza
                }
            }
            
        except Exception as e:
            print(f"❌ Error al realizar predicción para partido {partido_id}: {e}")
            return {"error": f"Error en la predicción: {e}"}
    
    def predecir_proximos_partidos(self, dias=7, min_valor=0.05, min_confianza=0.1):
        """
        Predice todos los partidos próximos y filtra por oportunidades de valor.
        """
        conn = conectar_db()
        if not conn:
            return []
            
        cursor = conn.cursor()
        
        try:
            # Buscar partidos próximos
            fecha_limite = datetime.now() + timedelta(days=dias)
            
            cursor.execute("""
                SELECT id 
                FROM partidos 
                WHERE fecha BETWEEN NOW() AND %s
                  AND terminado = FALSE
                ORDER BY fecha ASC
            """, (fecha_limite,))
            
            partidos = cursor.fetchall()
            
            predicciones_valor = []
            
            for (partido_id,) in partidos:
                # Predecir cada partido
                prediccion = self.predecir_partido(partido_id)
                
                if "error" in prediccion:
                    continue
                
                # Filtrar por valor y confianza
                mejor_valor = max(
                    prediccion["prediccion"]["valor_apuestas"]["local"],
                    prediccion["prediccion"]["valor_apuestas"]["empate"],
                    prediccion["prediccion"]["valor_apuestas"]["visitante"]
                )
                
                confianza = prediccion["prediccion"]["confianza"]
                
                if mejor_valor >= min_valor and confianza >= min_confianza:
                    predicciones_valor.append(prediccion)
            
            # Ordenar por valor esperado * confianza (ponderado)
            predicciones_valor.sort(
                key=lambda x: x["prediccion"]["valor_esperado"] * x["prediccion"]["confianza"],
                reverse=True
            )
            
            return predicciones_valor
            
        except Exception as e:
            print(f"❌ Error al predecir próximos partidos: {e}")
            return []
        finally:
            cursor.close()
            conn.close() 