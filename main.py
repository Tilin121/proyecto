import argparse
from database import crear_tablas
from extraccion_datos import obtener_partidos_proximos, extraer_estadisticas_historicas
from prediccion_servicio import ServicioPrediccion
from tabulate import tabulate
from datetime import datetime

def formatear_porcentaje(valor):
    """Formatea un valor como porcentaje."""
    return f"{valor * 100:.1f}%" if valor is not None else "N/A"

def formatear_decimal(valor):
    """Formatea un valor decimal."""
    return f"{valor:.2f}" if valor is not None else "N/A"

def formatear_fecha(fecha):
    """Formatea una fecha."""
    return fecha.strftime("%d/%m/%Y %H:%M") if fecha else "N/A"

def mostrar_prediccion(prediccion):
    """Muestra los detalles de una predicción."""
    if "error" in prediccion:
        print(f"❌ Error: {prediccion['error']}")
        return
    
    partido = prediccion["partido"]
    pred = prediccion["prediccion"]
    
    print("\n" + "=" * 80)
    print(f"🏆 {partido['liga']} - {formatear_fecha(partido['fecha'])}")
    print(f"⚽ {partido['local']} vs {partido['visitante']}")
    print("=" * 80)
    
    # Mostrar predicción
    print("\n📊 PREDICCIÓN:")
    print(f"▶️ Resultado más probable: {pred['resultado_nombre']} ({formatear_porcentaje(pred['probabilidades'][pred['resultado_nombre'].lower().replace('victoria ', '')])})") 
    
    # Mostrar probabilidades
    print("\n📋 Probabilidades:")
    probabilidades = [
        ["Victoria Local", formatear_porcentaje(pred['probabilidades']['local']), 
         formatear_decimal(partido['cuotas']['Local']), formatear_decimal(pred['valor_apuestas']['local'])],
        ["Empate", formatear_porcentaje(pred['probabilidades']['empate']), 
         formatear_decimal(partido['cuotas']['Empate']), formatear_decimal(pred['valor_apuestas']['empate'])],
        ["Victoria Visitante", formatear_porcentaje(pred['probabilidades']['visitante']), 
         formatear_decimal(partido['cuotas']['Visitante']), formatear_decimal(pred['valor_apuestas']['visitante'])]
    ]
    print(tabulate(probabilidades, headers=["Resultado", "Probabilidad", "Cuota", "Valor"], tablefmt="grid"))
    
    # Mostrar recomendación
    print("\n🎯 RECOMENDACIÓN:")
    print(f"▶️ Apuesta recomendada: {pred['apuesta_recomendada']}")
    print(f"▶️ Valor esperado: {formatear_decimal(pred['valor_esperado'])}")
    print(f"▶️ Confianza: {formatear_porcentaje(pred['confianza'])}")
    
    # Nivel de confianza visual
    if pred['confianza'] >= 0.2:
        confianza = "ALTA"
    elif pred['confianza'] >= 0.1:
        confianza = "MEDIA"
    else:
        confianza = "BAJA"
        
    print(f"▶️ Nivel de confianza: {confianza}")
    
    # Interpretación del valor esperado
    if pred['valor_esperado'] >= 0.2:
        calidad = "EXCELENTE"
    elif pred['valor_esperado'] >= 0.1:
        calidad = "BUENA"
    elif pred['valor_esperado'] >= 0.05:
        calidad = "ACEPTABLE"
    else:
        calidad = "BAJA"
        
    print(f"▶️ Calidad de la apuesta: {calidad}")
    
    print("\n" + "=" * 80)

def mostrar_predicciones_multiples(predicciones):
    """Muestra una tabla con múltiples predicciones."""
    if not predicciones:
        print("\n⚠️ No se encontraron predicciones con valor suficiente.")
        return
    
    filas = []
    for pred in predicciones:
        partido = pred["partido"]
        p = pred["prediccion"]
        
        filas.append([
            formatear_fecha(partido['fecha']),
            partido['liga'],
            f"{partido['local']} vs {partido['visitante']}",
            p['apuesta_recomendada'],
            formatear_decimal(partido['cuotas'][p['apuesta_recomendada'].replace('Victoria ', '')]),
            formatear_porcentaje(p['probabilidades'][p['apuesta_recomendada'].lower().replace('victoria ', '')]),
            formatear_decimal(p['valor_esperado']),
            formatear_porcentaje(p['confianza'])
        ])
    
    print("\n" + "=" * 100)
    print("🏆 PREDICCIONES DE VALOR")
    print("=" * 100)
    
    print(tabulate(filas, headers=[
        "Fecha", "Liga", "Partido", "Apuesta", "Cuota", 
        "Probabilidad", "Valor", "Confianza"
    ], tablefmt="grid"))
    
    print("\n" + "=" * 100)

def mostrar_estadisticas_modelo(stats):
    """Muestra estadísticas de rendimiento del modelo."""
    if not stats:
        print("\n⚠️ No hay suficientes datos para mostrar estadísticas del modelo.")
        return
    
    print("\n" + "=" * 80)
    print("📈 ESTADÍSTICAS DEL MODELO")
    print("=" * 80)
    
    print(f"▶️ Total de predicciones evaluadas: {stats['total_predicciones']}")
    print(f"▶️ Predicciones acertadas: {stats['acertadas']}")
    print(f"▶️ Tasa de acierto: {formatear_porcentaje(stats['tasa_acierto'])}")
    print(f"▶️ Retorno de inversión (ROI): {formatear_porcentaje(stats['retorno_inversion'] / 100)}")
    
    print("\n" + "=" * 80)

def main():
    parser = argparse.ArgumentParser(description='Sistema de Predicción de Apuestas Deportivas')
    
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponibles')
    
    # Comando para configurar la base de datos