import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Asegurarnos que la carpeta modelos existe
os.makedirs("/root/proyecto/modelos", exist_ok=True)

# Crear un modelo básico
modelo = RandomForestClassifier(n_estimators=10)
modelo.fit(np.array([[1, 2, 3], [4, 5, 6]]), np.array([0, 1]))

# Crear un scaler
scaler = StandardScaler()
scaler.fit(np.array([[1, 2, 3], [4, 5, 6]]))

# Guardar el modelo y el scaler
joblib.dump(modelo, "/root/proyecto/modelos/prediccion_model.pkl")
joblib.dump(scaler, "/root/proyecto/modelos/prediccion_scaler.pkl")
print("✅ Modelo de prueba creado con éxito en /root/proyecto/modelos/")
