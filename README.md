# Sistema de Predicción de Apuestas Deportivas

Un sistema de predicción para apuestas deportivas basado en Machine Learning que extrae datos mediante web scraping, procesa la información y ofrece predicciones con valor.

## Características principales

- 🔍 **Web Scraping**: Extracción automática de datos de ligas, equipos, partidos y estadísticas desde fuentes como FootyStats y FBRef.
- 🧠 **Modelo de predicción**: Utiliza Random Forest para predecir resultados de partidos con probabilidades.
- 💰 **Análisis de valor**: Compara probabilidades con cuotas para identificar apuestas con valor esperado positivo.
- 📊 **Interfaz web**: Panel de control intuitivo para visualizar predicciones y estadísticas.
- 📈 **Seguimiento de rendimiento**: Monitoreo de la precisión del modelo y el retorno de inversión.

## Estructura del proyecto

```
proyecto/
├── config.py                 # Configuración y conexión a la base de datos
├── database.py               # Creación y gestión de tablas
├── main.py                   # Punto de entrada de la aplicación CLI
├── app.py                    # Aplicación web Flask
├── modelo_prediccion.py      # Implementación del modelo ML
├── prediccion_servicio.py    # Lógica de predicción y evaluación
├── extraccion_datos.py       # Módulos de web scraping mejorados
├── scrapers/                 # Módulos originales de web scraping
│   ├── scraper_fbref.py      # Extracción de datos de FBRef
│   └── scraper_footystats.py # Extracción de datos de FootyStats
├── modelos/                  # Modelos entrenados guardados
├── templates/                # Plantillas HTML para la interfaz web
└── README.md                 # Documentación
```

## Requisitos

- Python 3.7+
- PostgreSQL
- Dependencias (ver requirements.txt)

## Instalación

1. Clona el repositorio
```bash
git clone https://github.com/tu-usuario/prediccion-apuestas.git
cd prediccion-apuestas
```

2. Crea un entorno virtual e instala las dependencias
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configura la base de datos PostgreSQL en config.py

4. Inicializa la base de datos
```bash
python3 main.py setup
```

## Uso

### Línea de comandos

```bash
# Configurar la base de datos
python3 main.py setup

# Extraer datos (partidos próximos y estadísticas)
python3 main.py extraer --dias 7

# Entrenar el modelo
python3 main.py entrenar

# Predecir un partido específico
python3 main.py predecir <partido_id>

# Predecir todos los partidos próximos
python3 main.py proximos --dias 7 --min-valor 0.05 --min-confianza 0.1

# Actualizar predicciones pasadas
python3 main.py actualizar

# Ver estadísticas del modelo
python3 main.py stats --dias 60
```

### Interfaz web

Inicia la aplicación web:
```bash
python3 app.py
```

Accede a la interfaz desde tu navegador: http://localhost:5000

## Cómo funciona el modelo de predicción

El sistema utiliza un enfoque de aprendizaje supervisado basado en Random Forest que:

1. **Extrae datos históricos** de partidos, estadísticas de equipos y cuotas.
2. **Procesa características relevantes** como goles a favor/contra, posesión, xG, etc.
3. **Entrena el modelo** para predecir la probabilidad de victoria local, empate o victoria visitante.
4. **Compara las probabilidades con las cuotas** para identificar oportunidades de valor.
5. **Evalúa continuamente** el rendimiento del modelo con nuevos resultados.

## Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Realiza tus cambios y haz commit (`git commit -m 'Añadir nueva característica'`)
4. Sube los cambios a tu fork (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## Descargo de responsabilidad

Este sistema está creado con fines educativos e informativos. El uso de este software para realizar apuestas reales es bajo su propio riesgo. No nos hacemos responsables de las pérdidas económicas que puedan derivarse del uso de este sistema. Recuerde apostar de manera responsable.