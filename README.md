# Análisis de Mortalidad en Colombia 2019

Esta aplicación web interactiva muestra visualizaciones de los datos de mortalidad en Colombia durante el año 2019.

## Características

- Mapa de distribución de muertes por departamento
- Gráfico de líneas de muertes mensuales
- Gráfico de barras de ciudades más violentas
- Gráfico circular de ciudades con menor mortalidad
- Tabla de principales causas de muerte
- Histograma de distribución por edad
- Gráfico de barras apiladas por sexo y departamento

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd <nombre-del-directorio>
```

2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación localmente:
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:8050`

## Despliegue

La aplicación está configurada para ser desplegada en plataformas PaaS como Render, Railway, Google App Engine o AWS.

### Render

1. Crear una cuenta en Render
2. Crear un nuevo Web Service
3. Conectar con el repositorio de GitHub
4. Configurar:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:server`

### Railway

1. Crear una cuenta en Railway
2. Crear un nuevo proyecto
3. Conectar con el repositorio de GitHub
4. La aplicación se desplegará automáticamente

### Google App Engine

1. Instalar Google Cloud SDK
2. Ejecutar:
```bash
gcloud init
gcloud app deploy
```

## Estructura de Datos

La aplicación utiliza tres archivos Excel:
- `NoFetal2019.xlsx`: Datos de mortalidad
- `CodigosDeMuerte.xlsx`: Nombres de los códigos de causas
- `Divipola.xlsx`: División Político-Administrativa de Colombia

## Licencia

Este proyecto está bajo la Licencia MIT.
