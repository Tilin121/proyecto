import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import joblib
from config import conectar_db

class ModeloPrediccion:
    def __init__(self, ruta_modelo=None):
        """Inicializa el modelo de predicción."""
        self.model = None
        self.scaler = StandardScaler()
        if ruta_modelo:
            self.cargar_modelo(ruta_modelo)
    
    def obtener_datos_entrenamiento(self):
        """Obtiene los datos de entrenamiento desde la base de datos."""
        conn = conectar_db()
        if not conn:
            return None, None
        
        try:
            # Consulta SQL para obtener datos históricos de partidos
            # Esta consulta debe adaptarse a tu estructura de base de datos
            query = """
                SELECT 
                    e.nombre AS equipo_local,
                    e2.nombre AS equipo_visitante,
                    p.goles_local,
                    p.goles_visitante,
                    p.fecha,
                    l.nombre AS liga,
                    ej1.minutos_jugados AS min_local,
                    ej1.goles AS goles_hist_local,
                    ej1.asistencias AS asist_hist_local,
                    ej1.tarjetas_amarillas AS amarillas_hist_local,
                    ej1.tarjetas_rojas AS rojas_hist_local,
                    ej2.minutos_jugados AS min_visitante,
                    ej2.goles AS goles_hist_visitante,
                    ej2.asistencias AS asist_hist_visitante,
                    ej2.tarjetas_amarillas AS amarillas_hist_visitante,
                    ej2.tarjetas_rojas AS rojas_hist_visitante,
                    c1.valor AS cuota_local,
                    c2.valor AS cuota_visitante,
                    c3.valor AS cuota_empate
                FROM partidos p
                JOIN equipos e ON p.equipo_local_id = e.id
                JOIN equipos e2 ON p.equipo_visitante_id = e2.id
                JOIN ligas l ON e.liga_id = l.id
                LEFT JOIN estadisticas_jugadores ej1 ON ej1.equipo_id = e.id
                LEFT JOIN estadisticas_jugadores ej2 ON ej2.equipo_id = e2.id
                LEFT JOIN cuotas c1 ON c1.partido_id = p.id AND c1.tipo_apuesta = 'Local'
                LEFT JOIN cuotas c2 ON c2.partido_id = p.id AND c2.tipo_apuesta = 'Visitante'
                LEFT JOIN cuotas c3 ON c3.partido_id = p.id AND c3.tipo_apuesta = 'Empate'
                WHERE p.fecha < NOW() - INTERVAL '1 day'
                ORDER BY p.fecha DESC
            """
            
            # Cargar datos en un DataFrame
            df = pd.read_sql_query(query, conn)
            
            # Cerrar conexión
            conn.close()
            
            # Crear la columna de resultado (0: local, 1: empate, 2: visitante)
            df['resultado'] = np.where(df['goles_local'] > df['goles_visitante'], 0,
                                      np.where(df['goles_local'] == df['goles_visitante'], 1, 2))
            
            # Seleccionar características (features) y objetivo (target)
            features = [
                'min_local', 'goles_hist_local', 'asist_hist_local', 'amarillas_hist_local', 'rojas_hist_local',
                'min_visitante', 'goles_hist_visitante', 'asist_hist_visitante', 'amarillas_hist_visitante', 'rojas_hist_visitante',
                'cuota_local', 'cuota_visitante', 'cuota_empate'
            ]
            
            # Manejar valores nulos - estrategia simple de reemplazo por la media
            for col in features:
                df[col] = df[col].fillna(df[col].mean() if df[col].mean() > 0 else 0)
            
            X = df[features]
            y = df['resultado']
            
            return X, y
            
        except Exception as e:
            print(f"❌ Error al obtener datos de entrenamiento: {e}")
            conn.close()
            return None, None
    
    def entrenar_modelo(self, guardar_ruta=None):
        """Entrena el modelo de predicción y opcionalmente lo guarda en un archivo."""
        # Obtener datos
        X, y = self.obtener_datos_entrenamiento()
        
        if X is None or y is None:
            print("❌ No se pudieron obtener datos para entrenar el modelo.")
            return False
        
        if len(X) < 50:  # Verificar que hay suficientes datos
            print(f"⚠️ Pocos datos para entrenar ({len(X)}). El modelo puede no ser preciso.")
        
        # Dividir en conjuntos de entrenamiento y prueba
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Escalar características
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Crear y entrenar el modelo
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluar el modelo
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"✅ Modelo entrenado con precisión: {accuracy:.4f}")
        print("\nInforme de clasificación:")
        print(classification_report(y_test, y_pred, target_names=['Local', 'Empate', 'Visitante']))
        
        # Guardar el modelo si se proporciona una ruta
        if guardar_ruta:
            try:
                joblib.dump(self.model, f"{guardar_ruta}_model.pkl")
                joblib.dump(self.scaler, f"{guardar_ruta}_scaler.pkl")
                print(f"✅ Modelo guardado en {guardar_ruta}_model.pkl")
                return True
            except Exception as e:
                print(f"❌ Error al guardar el modelo: {e}")
                return False
        
        return True
    
    def cargar_modelo(self, ruta_base):
        """Carga un modelo previamente entrenado."""
        try:
            self.model = joblib.load(f"{ruta_base}_model.pkl")
            self.scaler = joblib.load(f"{ruta_base}_scaler.pkl")
            print(f"✅ Modelo cargado desde {ruta_base}_model.pkl")
            return True
        except Exception as e:
            print(f"❌ Error al cargar el modelo: {e}")
            return False
    
    def predecir_partido(self, datos_partido):
        """
        Predice el resultado de un partido.
        
        Args:
            datos_partido: DataFrame con las características del partido a predecir
                           (mismas columnas que las usadas en el entrenamiento)
        
        Returns:
            resultado: int (0: local, 1: empate, 2: visitante)
            probabilidades: list de probabilidades para cada resultado
        """
        if self.model is None:
            print("❌ El modelo no está entrenado o cargado.")
            return None, None
        
        # Escalar datos
        datos_escalados = self.scaler.transform(datos_partido)
        
        # Predecir
        resultado = self.model.predict(datos_escalados)[0]
        probabilidades = self.model.predict_proba(datos_escalados)[0]
        
        return resultado, probabilidades
    
    def evaluar_valor_apuesta(self, probabilidades, cuotas):
        """
        Evalúa el valor de una apuesta comparando probabilidades con cuotas.
        
        Args:
            probabilidades: Array con probabilidades [local, empate, visitante]
            cuotas: Array con cuotas [local, empate, visitante]
        
        Returns:
            valor_apuesta: Array con el valor esperado [local, empate, visitante]
        """
        # El valor de la apuesta es la probabilidad * cuota - 1
        # Si es positivo, la apuesta tiene valor esperado positivo
        valor_apuesta = [prob * cuota - 1 for prob, cuota in zip(probabilidades, cuotas)]
        
        return valor_apuesta