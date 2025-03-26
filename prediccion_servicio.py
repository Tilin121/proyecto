import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import conectar_db
from modelo_prediccion import ModeloPrediccion

class ServicioPrediccion:
    def __init__(self, ruta_modelo=None):
        """Inicializa el servicio de predicción."""
        self.modelo = ModeloPrediccion(ruta_modelo)
        
        # Si no hay modelo cargado, entrenar uno nuevo
        if self.modelo.model is None and ruta_modelo is None:
            print("🔍 No se encontró un modelo cargado. Entrenando nuevo modelo...")
            self.modelo.entrenar_modelo("modelos/prediccion")
    
    def _obtener_estadisticas_equipo(self, equipo_id, es_local=True, partidos=5):
        """
        Obtiene estadísticas históricas de un equipo para los últimos N partidos.
        
        Args:
            equipo_id: ID del equipo
            es_local: True si juega de local, False si es visitante
            partidos: Número de partidos a considerar
            
        Returns:
            dict: Diccionario con estadísticas agregadas
        """
        conn = conectar_db()
        if not conn:
            return {}
            
        cursor = conn.cursor()
        
        try:
            # Consultar últimos partidos del equipo
            cursor.execute("""
                SELECT 
                    goles_favor, 
                    goles_contra, 
                    posesion, 
                    xg, 
                    xga,
                    es_local
                FROM estadisticas_historicas 
                WHERE equipo_id = %s
                ORDER BY fecha DESC
                LIMIT %s
            """, (equipo_id, partidos))
            
            partidos_recientes = cursor.fetchall()
            
            if not partidos_recientes:
                return {
                    "goles_favor_media": 0,
                    "goles_contra_media": 0,
                    "posesion_media": 50,
                    "xg_media": 0,
                    "xga_media": 0,
                    "victorias": 0,
                    "empates": 0,
                    "derrotas": 0
                }
            
            # Calcular estadísticas
            goles_favor = [p[0] for p in partidos_recientes]
            goles_contra = [p[1] for p in partidos_recientes]
            posesion = [p[2] for p in partidos_recientes if p[2] is not None]
            xg = [p[3] for p in partidos_recientes if p[3] is not None]
            xga = [p[4] for p in partidos_recientes if p[4] is not None]
            
            # Calcular victorias, empates y derrotas
            victorias = sum(1 for i in range(len(partidos_recientes)) if goles_favor[i] > goles_contra[i])
            empates = sum(1 for i in range(len(partidos_recientes)) if goles_favor[i] == goles_contra[i])
            derrotas = sum(1 for i in range(len(partidos_recientes)) if goles_favor[i] < goles_contra[i])
            
            # Filtrar por condición (local/visitante) si es necesario
            if es_local is not None:
                partidos_condicion = [i for i, p in enumerate(partidos_recientes) if p[5] == es_local]
                if partidos_condicion:
                    goles_favor_condicion = [goles_favor[i] for i in partidos_condicion]
                    goles_contra_condicion = [goles_contra[i] for i in partidos_condicion]
                else:
                    goles_favor_condicion = goles_favor
                    goles_contra_condicion = goles_contra
            else:
                goles_favor_condicion = goles_favor
                goles_contra_condicion = goles_contra
            
            # Calcular tendencia (últimos 3 vs anteriores)
            if len(goles_favor) >= 5:
                tendencia_goles = sum(goles_favor[:3]) / 3 - sum(goles_favor[3:]) / (len(goles_favor) - 3)
            else:
                tendencia_goles = 0
                
            return {
                "goles_favor_media": sum(goles_favor) / len(goles_favor) if goles_favor else 0,
                "goles_contra_media": sum(goles_contra) / len(goles_contra) if goles_contra else 0,
                "posesion_media": sum(posesion) / len(posesion) if posesion else 50,
                "xg_media": sum(xg) / len(xg) if xg else 1.0,
                "xga_media": sum(xga) / len(xga) if xga else 1.0,
                "victorias": victorias,
                "empates": empates,
                "derrotas": derrotas,
                "tendencia_goles": tendencia_goles,
                "goles_favor_condicion": sum(goles_favor_condicion) / len(goles_favor_condicion) if goles_favor_condicion else 0,
                "goles_contra_condicion": sum(goles_contra_condicion) / len(goles_contra_condicion) if goles_contra_condicion else 0
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
        
        Args:
            partido_id: ID del partido a predecir
            
        Returns:
            DataFrame: Datos preparados para el modelo
            dict: Información adicional del partido (equipos, cuotas, etc.)
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
                    el.id AS equipo_local_id, 
                    el.nombre AS equipo_local,
                    ev.id AS equipo_visitante_id, 
                    ev.nombre AS equipo_visitante,
                    l.nombre AS liga,
                    p.fecha
                FROM partidos p
                JOIN equipos el ON p.equipo_local_id = el.id
                JOIN equipos ev ON p.equipo_visitante_id = ev.id
                JOIN ligas l ON p.liga_id = l.id
                WHERE p.id = %s
            """, (partido_id,))
            
            partido = cursor.fetchone()
            
            if not partido:
                print(f"❌ No se encontró el partido con ID {partido_id}")
                return None, None
                
            partido_id, local_id, local_nombre, visitante_id, visitante_nombre, liga, fecha = partido
            
            # Obtener cuotas
            cursor.execute("""
                SELECT tipo_apuesta, valor, casa_apuestas
                FROM cuotas
                WHERE partido_id = %s
                ORDER BY fecha DESC
            """, (partido_id,))
            
            cuotas_raw = cursor.fetchall()
            cuotas = {"Local": None, "Empate": None, "Visitante": None}
            
            for tipo, valor, casa in cuotas_raw:
                if tipo in cuotas and cuotas[tipo] is None:
                    cuotas[tipo] = valor
            
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
                "cuota_local": cuotas["Local"] if cuotas["Local"] else 2.0,
                "cuota_empate": cuotas["Empate"] if cuotas["Empate"] else 3.0,
                "cuota_visitante": cuotas["Visitante"] if cuotas["Visitante"] else 3.5,
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
        
        Args:
            partido_id: ID del partido a predecir
            
        Returns:
            dict: Resultado de la predicción con probabilidades y recomendaciones
        """
        # Preparar datos
        datos, info = self.preparar_datos_partido(partido_id)
        
        if datos is None or info is None:
            return {"error": "No se pudieron obtener los datos del partido"}
        
        # Realizar predicción
        try:
            resultado, probabilidades = self.modelo.predecir_partido(datos)
            
            # Evaluar valor de las apuestas
            cuotas = [
                info["cuotas"]["Local"] if info["cuotas"]["Local"] else 2.0,
                info["cuotas"]["Empate"] if info["cuotas"]["Empate"] else 3.0,
                info["cuotas"]["Visitante"] if info["cuotas"]["Visitante"] else 3.5
            ]
            
            valor_apuestas = self.modelo.evaluar_valor_apuesta(probabilidades, cuotas)
            
            # Determinar apuesta recomendada
            mejor_valor_idx = np.argmax(valor_apuestas)
            mejor_valor = valor_apuestas[mejor_valor_idx]
            
            resultados = ["Victoria Local", "Empate", "Victoria Visitante"]
            
            # Confianza (diferencia entre la mayor probabilidad y la siguiente)
            probs_ordenadas = sorted(probabilidades, reverse=True)
            confianza = probs_ordenadas[0] - probs_ordenadas[1]
            
            # Guardar predicción en la base de datos
            self._guardar_prediccion(
                partido_id, 
                probabilidades, 
                resultado, 
                valor_apuestas,
                confianza
            )
            
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
        
        Args:
            dias: Número de días en el futuro
            min_valor: Valor mínimo esperado para recomendar
            min_confianza: Confianza mínima para recomendar
            
        Returns:
            list: Lista de predicciones con valor
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
    
    def _guardar_prediccion(self, partido_id, probabilidades, resultado, valores, confianza):
        """
        Guarda la predicción en la base de datos.
        """
        conn = conectar_db()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO predicciones 
                (partido_id, fecha_prediccion, prob_local, prob_empate, prob_visitante, 
                 resultado_predicho, valor_local, valor_empate, valor_visitante, confianza)
                VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (partido_id, fecha_prediccion) DO UPDATE
                SET prob_local = EXCLUDED.prob_local,
                    prob_empate = EXCLUDED.prob_empate,
                    prob_visitante = EXCLUDED.prob_visitante,
                    resultado_predicho = EXCLUDED.resultado_predicho,
                    valor_local = EXCLUDED.valor_local,
                    valor_empate = EXCLUDED.valor_empate,
                    valor_visitante = EXCLUDED.valor_visitante,
                    confianza = EXCLUDED.confianza
            """, (
                partido_id, 
                probabilidades[0], probabilidades[1], probabilidades[2],
                resultado,
                valores[0], valores[1], valores[2],
                confianza
            ))
            
            conn.commit()
            print(f"✅ Predicción guardada para partido {partido_id}")
            
        except Exception as e:
            print(f"❌ Error al guardar predicción para partido {partido_id}: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    def actualizar_predicciones_pasadas(self):
        """
        Actualiza el campo 'acertada' en las predicciones de partidos ya terminados.
        """
        conn = conectar_db()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        try:
            # Buscar predicciones sin evaluar de partidos terminados
            cursor.execute("""
                SELECT 
                    pred.id, 
                    pred.partido_id, 
                    pred.resultado_predicho,
                    p.goles_local,
                    p.goles_visitante
                FROM predicciones pred
                JOIN partidos p ON pred.partido_id = p.id
                WHERE pred.acertada IS NULL
                  AND p.terminado = TRUE
                  AND p.goles_local IS NOT NULL
                  AND p.goles_visitante IS NOT NULL
            """)
            
            predicciones = cursor.fetchall()
            
            for pred_id, partido_id, resultado_predicho, goles_local, goles_visitante in predicciones:
                # Determinar resultado real
                if goles_local > goles_visitante:
                    resultado_real = 0  # Victoria local
                elif goles_local == goles_visitante:
                    resultado_real = 1  # Empate
                else:
                    resultado_real = 2  # Victoria visitante
                
                # Comparar con predicción
                acertada = resultado_predicho == resultado_real
                
                # Actualizar en BD
                cursor.execute("""
                    UPDATE predicciones
                    SET acertada = %s
                    WHERE id = %s
                """, (acertada, pred_id))
                
                print(f"✅ Predicción {pred_id} evaluada como {'acertada' if acertada else 'fallida'}")
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error al actualizar predicciones pasadas: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    def obtener_stats_modelo(self, dias=60):
        """
        Obtiene estadísticas de rendimiento del modelo.
        
        Args:
            dias: Número de días hacia atrás para evaluar
            
        Returns:
            dict: Estadísticas del modelo
        """
        conn = conectar_db()
        if not conn:
            return {}
            
        cursor = conn.cursor()
        
        try:
            # Fecha límite
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            # Obtener predicciones evaluadas
            cursor.execute("""
                SELECT 
                    acertada,
                    resultado_predicho,
                    prob_local,
                    prob_empate,
                    prob_visitante,
                    valor_local,
                    valor_empate,
                    valor_visitante
                FROM predicciones p
                JOIN partidos pt ON p.partido_id = pt.id
                WHERE p.acertada IS NOT NULL
                  AND pt.fecha > %s
            """, (fecha_limite,))
            
            predicciones = cursor.fetchall()
            
            if not predicciones:
                return {
                    "total_predicciones": 0,
                    "acertadas": 0,
                    "tasa_acierto": 0,
                    "retorno_inversion": 0
                }
            
            # Calcular estadísticas
            total = len(predicciones)
            acertadas = sum(1 for p in predicciones if p[0])
            
            # Calcular retorno de inversión
            inversion = total  # 1 unidad por apuesta
            retorno = 0
            
            for acertada, resultado, p_local, p_empate, p_visitante, v_local, v_empate, v_visitante in predicciones:
                if not acertada:
                    continue
                    
                # Si acertó, sumar la cuota correspondiente
                if resultado == 0:  # Local
                    # Cuota = (1 + valor) / probabilidad
                    cuota = (1 + v_local) / p_local if p_local > 0 else 0
                elif resultado == 1:  # Empate
                    cuota = (1 + v_empate) / p_empate if p_empate > 0 else 0
                else:  # Visitante
                    cuota = (1 + v_visitante) / p_visitante if p_visitante > 0 else 0
                
                retorno += cuota
            
            roi = (retorno - inversion) / inversion * 100 if inversion > 0 else 0
            
            return {
                "total_predicciones": total,
                "acertadas": acertadas,
                "tasa_acierto": acertadas / total if total > 0 else 0,
                "retorno_inversion": roi
            }
            
        except Exception as e:
            print(f"❌ Error al obtener estadísticas del modelo: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()