import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from config import conectar_db

class ModeloPrediccion:
    def __init__(self, ruta_modelo=None):
        """Inicializa el modelo de predicción."""
        self.model = None
        self.scaler = StandardScaler()
        
        if ruta_modelo:
            try:
                modelo_path = f"{ruta_modelo}_model.pkl"
                scaler_path = f"{ruta_modelo}_scaler.pkl"
                
                if os.path.exists(modelo_path) and os.path.exists(scaler_path):
                    self.model = joblib.load(modelo_path)
                    self.scaler = joblib.load(scaler_path)
                    print(f"✅ Modelo cargado desde {ruta_modelo}_model.pkl")
                else:
                    print(f"⚠️ No se encontraron archivos del modelo en {ruta_modelo}")
                    self._crear_modelo_basico()
            except Exception as e:
                print(f"❌ Error al cargar el modelo: {e}")
                self._crear_modelo_basico()
        else:
            self._crear_modelo_basico()
    
    def _crear_modelo_basico(self):
        """Crea un modelo básico para pruebas."""
        try:
            # Crear un dataset de prueba
            X = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 2.0, 3.0, 3.5],
                          [4, 3, 2, 1, 5, 6, 7, 8, 9, 10, 1.8, 3.2, 3.1]])
            y = np.array([0, 2])  # Victoria local, Victoria visitante
            
            # Escalar características
            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)
            
            # Crear y entrenar el modelo
            self.model = RandomForestClassifier(n_estimators=10, random_state=42)
            self.model.fit(X_scaled, y)
            
            # Guardar el modelo
            os.makedirs("modelos", exist_ok=True)
            joblib.dump(self.model, "modelos/prediccion_model.pkl")
            joblib.dump(self.scaler, "modelos/prediccion_scaler.pkl")
            
            print("✅ Modelo básico creado con éxito")
        except Exception as e:
            print(f"❌ Error al crear modelo básico: {e}")
    
    def obtener_datos_entrenamiento(self):
        """Obtiene los datos de entrenamiento desde la base de datos."""
        # Para simplificar, devolvemos datos de prueba
        X = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 2.0, 3.0, 3.5],
                      [4, 3, 2, 1, 5, 6, 7, 8, 9, 10, 1.8, 3.2, 3.1]])
        y = np.array([0, 2])
        
        return pd.DataFrame(X), y
    
    def entrenar_modelo(self, guardar_ruta=None):
        """Entrena el modelo de predicción y opcionalmente lo guarda en un archivo."""
        X, y = self.obtener_datos_entrenamiento()
        
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)
        
        if guardar_ruta:
            try:
                os.makedirs(os.path.dirname(guardar_ruta) if guardar_ruta.find('/') > 0 else 'modelos', exist_ok=True)
                joblib.dump(self.model, f"{guardar_ruta}_model.pkl")
                joblib.dump(self.scaler, f"{guardar_ruta}_scaler.pkl")
                print(f"✅ Modelo guardado en {guardar_ruta}_model.pkl")
            except Exception as e:
                print(f"❌ Error al guardar el modelo: {e}")
        
        return True
    
    def predecir_partido(self, datos_partido):
        """Predice el resultado de un partido."""
        if self.model is None:
            self._crear_modelo_basico()
        
        # Escalar datos
        datos_escalados = self.scaler.transform(datos_partido)
        
        # Predecir
        resultado = self.model.predict(datos_escalados)[0]
        probabilidades = self.model.predict_proba(datos_escalados)[0]
        
        return resultado, probabilidades
    
    def evaluar_valor_apuesta(self, probabilidades, cuotas):
        """Evalúa el valor de una apuesta comparando probabilidades con cuotas."""
        valor_apuesta = [prob * cuota - 1 for prob, cuota in zip(probabilidades, cuotas)]
        return valor_apuesta