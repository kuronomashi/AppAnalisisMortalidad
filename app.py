import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import dash_bootstrap_components as dbc

# Loading the data
def load_data():
    # Data paths
    mortality_path = 'data/Anexo1.NoFetal2019_CE_15-03-23.xlsx'
    codes_path = 'data/Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx'
    divipola_path = 'data/Anexo3.Divipola_CE_15-03-23.xlsx'
    
    print("Cargando archivos...")
    
    # Load datasets
    mortality_df = pd.read_excel(mortality_path)
    print("\nColumnas de mortalidad:", mortality_df.columns.tolist())
    
    # Cargar códigos saltando las filas de metadatos
    codes_df = pd.read_excel(codes_path, skiprows=7)
    
    # Renombrar las columnas directamente basándonos en su posición
    codes_df.columns = ['capitulo', 'codigo', 'subcodigo', 'descripcion_corta', 'descripcion_larga', 'descripcion_completa']
    
    # Eliminar la primera fila que contiene los nombres de los capítulos
    codes_df = codes_df[codes_df['capitulo'] != 'Capítulo']
    
    # Limpiar los códigos de espacios y caracteres especiales
    codes_df['codigo'] = codes_df['codigo'].astype(str).str.strip()
    codes_df['subcodigo'] = codes_df['subcodigo'].astype(str).str.strip()
    
    # Crear el código completo combinando código y subcódigo
    codes_df['causa_basica'] = codes_df['codigo'] + codes_df['subcodigo']
    codes_df['causa_nombre'] = codes_df['descripcion_completa']
    
    print("\nPrimeras filas de códigos procesados:")
    print(codes_df[['causa_basica', 'causa_nombre']].head())
    
    divipola_df = pd.read_excel(divipola_path)
    print("\nColumnas de divipola:", divipola_df.columns.tolist())
    
    # Normalizar nombres de columnas
    mortality_df.columns = mortality_df.columns.str.lower()
    divipola_df.columns = divipola_df.columns.str.lower()
    
    # Renombrar columnas para que coincidan en ambos dataframes
    # Para divipola
    if 'cod_departamento' in divipola_df.columns:
        divipola_df.rename(columns={
            'cod_departamento': 'cod_depto',
            'cod_municipio': 'cod_muni',
            'departamento': 'departamento',
            'municipio': 'municipio'
        }, inplace=True)
    
    # Para mortalidad
    if 'cod_departamento' in mortality_df.columns:
        mortality_df.rename(columns={
            'cod_departamento': 'cod_depto',
            'cod_municipio': 'cod_muni',
            'grupo_edad1': 'grupo_edad',
            'sexo': 'sexo',
            'cod_muerte': 'causa_basica',
            'municipio': 'municipio',
            'departamento': 'departamento'
        }, inplace=True)
    
    # Convertir fecha si existe
    if 'fecha_defuncion' in mortality_df.columns:
        mortality_df['fecha_defuncion'] = pd.to_datetime(mortality_df['fecha_defuncion'], errors='coerce')
        mortality_df['mes'] = mortality_df['fecha_defuncion'].dt.month
    elif 'año' in mortality_df.columns and 'mes' in mortality_df.columns:
        mortality_df['fecha_defuncion'] = pd.to_datetime(mortality_df['año'].astype(str) + '-' + mortality_df['mes'].astype(str) + '-01', errors='coerce')
    
    # Asegurarse de que los tipos de datos coincidan
    mortality_df['cod_depto'] = mortality_df['cod_depto'].astype(str)
    mortality_df['cod_muni'] = mortality_df['cod_muni'].astype(str)
    mortality_df['causa_basica'] = mortality_df['causa_basica'].astype(str)
    
    divipola_df['cod_depto'] = divipola_df['cod_depto'].astype(str)
    divipola_df['cod_muni'] = divipola_df['cod_muni'].astype(str)
    
    print("\nValores únicos en causa_basica de mortalidad:")
    print(mortality_df['causa_basica'].unique()[:10])
    print("\nValores únicos en causa_basica de códigos:")
    print(codes_df['causa_basica'].unique()[:10])
    
    print("\nRealizando merge de datasets...")
    print("Columnas de mortalidad antes del merge:", mortality_df.columns.tolist())
    print("Columnas de divipola antes del merge:", divipola_df.columns.tolist())
    
    # Merge datasets
    mortality_with_geo = pd.merge(
        mortality_df, 
        divipola_df[['cod_depto', 'departamento', 'cod_muni', 'municipio']], 
        on=['cod_depto', 'cod_muni'], 
        how='left'
    )
    
    print("\nColumnas después del primer merge:", mortality_with_geo.columns.tolist())
    print("Número de filas después del primer merge:", len(mortality_with_geo))
    
    # Realizar el merge con los códigos
    full_data = pd.merge(
        mortality_with_geo,
        codes_df[['causa_basica', 'causa_nombre']],
        on='causa_basica',
        how='left'
    )
    
    print("\nColumnas después del segundo merge:", full_data.columns.tolist())
    print("Número de filas después del segundo merge:", len(full_data))
    
    # Verificar valores nulos en causa_nombre
    print("\nNúmero de valores nulos en causa_nombre:", full_data['causa_nombre'].isnull().sum())
    print("\nEjemplos de filas con causa_nombre nulo:")
    print(full_data[full_data['causa_nombre'].isnull()][['causa_basica', 'causa_nombre']].head())
    
    return full_data, divipola_df

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Load the data
try:
    full_data, divipola_df = load_data()
    data_loaded = True
except Exception as e:
    print(f"Error loading data: {e}")
    full_data = pd.DataFrame()
    divipola_df = pd.DataFrame()
    data_loaded = False

# Define age groups
def categorize_age(age):
    if pd.isna(age):
        return 'No especificado'
    try:
        age = int(age)
        if age <= 4:
            return '0-4'
        elif age <= 9:
            return '5-9'
        elif age <= 14:
            return '10-14'
        elif age <= 19:
            return '15-19'
        elif age <= 24:
            return '20-24'
        elif age <= 29:
            return '25-29'
        elif age <= 34:
            return '30-34'
        elif age <= 39:
            return '35-39'
        elif age <= 44:
            return '40-44'
        elif age <= 49:
            return '45-49'
        elif age <= 54:
            return '50-54'
        elif age <= 59:
            return '55-59'
        elif age <= 64:
            return '60-64'
        elif age <= 69:
            return '65-69'
        elif age <= 74:
            return '70-74'
        elif age <= 79:
            return '75-79'
        elif age <= 84:
            return '80-84'
        else:
            return '85+'
    except (ValueError, TypeError):
        return 'No especificado'

if data_loaded and 'grupo_edad' in full_data.columns:
    # Asegurarse de que grupo_edad sea numérico antes de aplicar la función
    full_data['grupo_edad'] = pd.to_numeric(full_data['grupo_edad'], errors='coerce')
    full_data['rango_edad'] = full_data['grupo_edad'].apply(categorize_age)

# Define app layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Análisis de Mortalidad en Colombia 2019",
                   className="text-center my-4"),
            html.P("Esta aplicación muestra visualizaciones interactivas de los datos de mortalidad en Colombia durante el año 2019.",
                   className="text-center mb-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H3('Distribución de Muertes por Departamento', 
                    style={'textAlign': 'center', 'color': '#2980b9'}),
            dcc.Graph(id='map-graph')
        ], className='six columns'),
        
        dbc.Col([
            html.H3('Muertes Mensuales en Colombia', 
                    style={'textAlign': 'center', 'color': '#2980b9'}),
            dcc.Graph(id='line-graph')
        ], className='six columns'),
    ], className='row'),
    
    dbc.Row([
        dbc.Col([
            html.H3('5 Ciudades más Violentas', 
                    style={'textAlign': 'center', 'color': '#2980b9'}),
            dcc.Graph(id='bar-violence-graph')
        ], className='six columns'),
        
        dbc.Col([
            html.H3('10 Ciudades con Menor Índice de Mortalidad', 
                    style={'textAlign': 'center', 'color': '#2980b9'}),
            dcc.Graph(id='pie-low-mortality-graph')
        ], className='six columns'),
    ], className='row'),
    
    dbc.Row([
        dbc.Col([
            html.H3('10 Principales Causas de Muerte', 
                    style={'textAlign': 'center', 'color': '#2980b9'}),
            dash_table.DataTable(
                id='table-causes',
                columns=[
                    {'name': 'Código', 'id': 'causa_basica'},
                    {'name': 'Causa de Muerte', 'id': 'causa_nombre'},
                    {'name': 'Total Casos', 'id': 'total_casos'}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '15px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_header={
                    'backgroundColor': '#2980b9',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f2f2f2'
                    }
                ]
            )
        ], width=12),
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H3('Distribución de Muertes por Edad', 
                    style={'textAlign': 'center', 'color': '#2980b9'}),
            dcc.Graph(id='histogram-age-graph')
        ], width=12),
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H3('Muertes por Sexo y Departamento', 
                    style={'textAlign': 'center', 'color': '#2980b9'}),
            dcc.Graph(id='stacked-bar-graph')
        ], width=12),
    ]),
    
    dbc.Row([
        dbc.Col([
            html.P('Desarrollado para el curso de Aplicaciones I - Universidad de La Salle © 2025',
                  style={'textAlign': 'center', 'marginTop': 30})
        ])
    ])
], fluid=True)

# Define callback for map
@app.callback(
    Output('map-graph', 'figure'),
    [Input('map-graph', 'id')]
)
def update_map(id):
    if not data_loaded:
        return go.Figure().update_layout(title="No se pudieron cargar los datos")
    
    # Calculate deaths by department
    deaths_by_dept = full_data.groupby('departamento').size().reset_index(name='total_muertes')
    
    # Colombia GeoJSON puede ser cargado de un repositorio público o incluido directamente
    # Por simplicidad, usaremos px.choropleth_mapbox que no requiere GeoJSON
    
    # Crear mapa utilizando plotly express con fallback a scatter mapbox
    try:
        # Puntos centrales aproximados de departamentos en Colombia
        # Esto es una aproximación - en una implementación real deberías tener coordenadas precisas
        dept_coords = {
            'ANTIOQUIA': (7.1986, -75.3412),
            'ATLANTICO': (10.6966, -74.8741),
            'BOGOTA': (4.7110, -74.0721),
            'BOLIVAR': (8.6704, -74.0299),
            'BOYACA': (5.4545, -73.3621),
            'CALDAS': (5.2983, -75.2479),
            'CAQUETA': (1.0102, -74.6535),
            'CAUCA': (2.4448, -76.8148),
            'CESAR': (9.3373, -73.6536),
            'CORDOBA': (8.0493, -75.5740),
            'CUNDINAMARCA': (5.0269, -74.0300),
            'CHOCO': (5.2528, -76.8260),
            'HUILA': (2.5359, -75.5277),
            'LA GUAJIRA': (11.3548, -72.5205),
            'MAGDALENA': (10.4113, -74.4057),
            'META': (3.9339, -73.0377),
            'NARIÑO': (1.2892, -77.3579),
            'NORTE DE SANTANDER': (7.9462, -72.8989),
            'QUINDIO': (4.5388, -75.6791),
            'RISARALDA': (5.3158, -75.9928),
            'SANTANDER': (6.6437, -73.6536),
            'SUCRE': (9.3048, -75.3971),
            'TOLIMA': (4.0925, -75.1545),
            'VALLE DEL CAUCA': (3.8009, -76.6413),
            'ARAUCA': (6.6413, -71.0004),
            'CASANARE': (5.7589, -71.5724),
            'PUTUMAYO': (0.4360, -76.8234),
            'SAN ANDRES': (12.5567, -81.7186),
            'AMAZONAS': (-1.0037, -71.9381),
            'GUAINIA': (2.5853, -68.5247),
            'GUAVIARE': (2.0412, -72.3322),
            'VAUPES': (0.8554, -70.8120),
            'VICHADA': (4.4234, -69.2872),
        }
        
        # Crear un dataframe con coordenadas
        map_data = []
        for idx, row in deaths_by_dept.iterrows():
            dept = row['departamento'].upper() if isinstance(row['departamento'], str) else 'DESCONOCIDO'
            if dept in dept_coords:
                lat, lon = dept_coords[dept]
                map_data.append({
                    'departamento': dept,
                    'total_muertes': row['total_muertes'],
                    'lat': lat,
                    'lon': lon
                })
        
        map_df = pd.DataFrame(map_data)
        
        # Crear mapa de burbujas interactivo
        fig = px.scatter_mapbox(
            map_df,
            lat='lat',
            lon='lon',
            size='total_muertes',
            color='total_muertes',
            hover_name='departamento',
            hover_data=['total_muertes'],
            color_continuous_scale='YlOrRd',
            size_max=40,
            zoom=5,
            mapbox_style='carto-positron',
            title='Distribución de Muertes por Departamento en Colombia (2019)',
            labels={'total_muertes': 'Total Muertes'}
        )
        
        fig.update_layout(
            height=600,
            margin={"r":0,"t":40,"l":0,"b":0},
        )
        
    except Exception as e:
        print(f"Error creating map: {e}")
        # Fallback to simple bar chart if map fails
        fig = px.bar(
            deaths_by_dept.sort_values('total_muertes', ascending=False),
            x='departamento',
            y='total_muertes',
            color='total_muertes',
            color_continuous_scale='YlOrRd',
            title='Distribución de Muertes por Departamento en Colombia (2019)',
            labels={'total_muertes': 'Total Muertes', 'departamento': 'Departamento'}
        )
        
        fig.update_layout(
            height=600,
            xaxis_title='Departamento',
            yaxis_title='Total Muertes',
            xaxis={'categoryorder':'total descending'}
        )
    
    return fig

# Define callback for line graph
@app.callback(
    Output('line-graph', 'figure'),
    [Input('line-graph', 'id')]
)
def update_line_graph(id):
    if not data_loaded:
        return go.Figure().update_layout(title="No se pudieron cargar los datos mensuales")
    
    # Calculate deaths by month
    if 'mes' in full_data.columns:
        deaths_by_month = full_data.groupby('mes').size().reset_index(name='total_muertes')
        deaths_by_month = deaths_by_month.sort_values('mes')
        
        # Map month numbers to names
        month_names = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        deaths_by_month['mes_nombre'] = deaths_by_month['mes'].map(month_names)
        
        # Create line chart
        fig = px.line(
            deaths_by_month, 
            x='mes_nombre', 
            y='total_muertes',
            markers=True,
            title='Total de Muertes por Mes en Colombia (2019)',
            labels={'total_muertes': 'Total Muertes', 'mes_nombre': 'Mes'}
        )
        
        fig.update_layout(
            height=500,
            xaxis_title='Mes',
            yaxis_title='Total Muertes',
            hovermode='x unified'
        )
    else:
        fig = go.Figure().update_layout(
            title="No se pudieron cargar los datos mensuales (columna 'mes' no encontrada)",
            height=500
        )
    
    return fig

# Define callback for violent cities bar graph
@app.callback(
    Output('bar-violence-graph', 'figure'),
    [Input('bar-violence-graph', 'id')]
)
def update_violence_graph(id):
    if not data_loaded:
        return go.Figure().update_layout(title="No se pudieron cargar los datos")
    
    try:
        # Filter homicides (agresión con disparo de armas de fuego - X95 o códigos similares)
        # Asegurarse de que causa_basica sea string antes de aplicar str.contains
        full_data['causa_basica'] = full_data['causa_basica'].astype(str)
        homicides = full_data[full_data['causa_basica'].str.contains('X95|X93|X94|X99', na=False, regex=True)]
        
        # Calculate homicides by city
        homicides_by_city = homicides.groupby('municipio').size().reset_index(name='total_homicidios')
        homicides_by_city = homicides_by_city.sort_values('total_homicidios', ascending=False).head(5)
        
        # Create bar chart
        fig = px.bar(
            homicides_by_city,
            x='municipio',
            y='total_homicidios',
            color='total_homicidios',
            color_continuous_scale='Reds',
            title='5 Ciudades más Violentas de Colombia (2019)',
            labels={'total_homicidios': 'Total Homicidios', 'municipio': 'Ciudad'}
        )
        
        fig.update_layout(
            height=500,
            xaxis_title='Ciudad',
            yaxis_title='Total Homicidios',
            coloraxis_showscale=False
        )
    except Exception as e:
        print(f"Error creating violence graph: {e}")
        fig = go.Figure().update_layout(
            title="Error al crear el gráfico de ciudades violentas",
            height=500
        )
    
    return fig

# Define callback for low mortality cities pie chart
@app.callback(
    Output('pie-low-mortality-graph', 'figure'),
    [Input('pie-low-mortality-graph', 'id')]
)
def update_low_mortality_graph(id):
    if not data_loaded:
        return go.Figure().update_layout(title="No se pudieron cargar los datos")
    
    try:
        # Calculate deaths by city (excluding cities with very few cases)
        deaths_by_city = full_data.groupby('municipio').size().reset_index(name='total_muertes')
        # Filtrar para tener sólo municipios con nombre válido
        deaths_by_city = deaths_by_city[deaths_by_city['municipio'].notna() & (deaths_by_city['municipio'] != '')]
        deaths_by_city = deaths_by_city[deaths_by_city['total_muertes'] > 50]  # Aumentar el umbral mínimo
        deaths_by_city = deaths_by_city.sort_values('total_muertes').head(10)
        
        # Create pie chart
        fig = px.pie(
            deaths_by_city,
            values='total_muertes',
            names='municipio',
            title='10 Ciudades con Menor Índice de Mortalidad',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        
        fig.update_layout(
            height=500,
            legend_title='Ciudad'
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
    except Exception as e:
        print(f"Error creating low mortality pie chart: {e}")
        fig = go.Figure().update_layout(
            title="Error al crear el gráfico de ciudades con baja mortalidad",
            height=500
        )
    
    return fig

# Define callback for main causes table
@app.callback(
    Output('table-causes', 'data'),
    [Input('table-causes', 'id')]
)
def update_causes_table(id):
    if not data_loaded:
        return []
    
    try:
        # Calculate deaths by cause
        # Agrupar por causa_basica primero y luego realizar un join con un dataframe
        # que tiene la correspondencia única entre causa_basica y causa_nombre
        
        # 1. Contar muertes por causa_basica
        deaths_by_causa = full_data.groupby('causa_basica').size().reset_index(name='total_casos')
        
        # 2. Crear un dataframe con la correspondencia única causa_basica -> causa_nombre
        causa_nombres = full_data.dropna(subset=['causa_basica', 'causa_nombre'])[['causa_basica', 'causa_nombre']].drop_duplicates()
        
        # 3. Unir los dataframes
        causes = pd.merge(
            deaths_by_causa,
            causa_nombres,
            on='causa_basica',
            how='left'
        )
        
        # 4. Ordenar y obtener top 10
        causes = causes.sort_values('total_casos', ascending=False).head(10)
        
        # 5. Limpiar nombres de causas
        causes['causa_nombre'] = causes['causa_nombre'].fillna('No especificado')
        
        return causes.to_dict('records')
    except Exception as e:
        print(f"Error generating causes table: {e}")
        return []

# Define callback for age distribution histogram
@app.callback(
    Output('histogram-age-graph', 'figure'),
    [Input('histogram-age-graph', 'id')]
)
def update_age_histogram(id):
    if not data_loaded:
        return go.Figure().update_layout(title="No se pudieron cargar los datos de edad")
    
    try:
        # Verificar si ya tenemos la columna rango_edad
        if 'rango_edad' not in full_data.columns:
            # Convertir grupo_edad a numérico si no lo es
            full_data['grupo_edad'] = pd.to_numeric(full_data['grupo_edad'], errors='coerce')
            # Aplicar la función de categorización
            full_data['rango_edad'] = full_data['grupo_edad'].apply(categorize_age)
        
        # Calculate deaths by age group
        deaths_by_age = full_data.groupby('rango_edad').size().reset_index(name='total_muertes')
        
        # Define age order for proper display
        age_order = [
            '0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39',
            '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74',
            '75-79', '80-84', '85+', 'No especificado'
        ]
        
        # Sort by defined order
        deaths_by_age['rango_edad'] = pd.Categorical(
            deaths_by_age['rango_edad'], 
            categories=age_order, 
            ordered=True
        )
        deaths_by_age = deaths_by_age.sort_values('rango_edad')
        
        # Eliminar 'No especificado' si no queremos mostrarlo
        if 'No especificado' in deaths_by_age['rango_edad'].values:
            no_spec_data = deaths_by_age[deaths_by_age['rango_edad'] == 'No especificado']
            if not no_spec_data.empty and no_spec_data['total_muertes'].iloc[0] < deaths_by_age['total_muertes'].max() * 0.05:
                deaths_by_age = deaths_by_age[deaths_by_age['rango_edad'] != 'No especificado']
        
        # Create histogram
        fig = px.bar(
            deaths_by_age,
            x='rango_edad',
            y='total_muertes',
            title='Distribución de Muertes por Rangos de Edad Quinquenales',
            labels={'total_muertes': 'Total Muertes', 'rango_edad': 'Rango de Edad'},
            color='total_muertes',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            height=500,
            xaxis_title='Rango de Edad',
            yaxis_title='Total Muertes',
            coloraxis_showscale=False
        )
    except Exception as e:
        print(f"Error creating age histogram: {e}")
        fig = go.Figure().update_layout(
            title="Error al crear el histograma de edades",
            height=500
        )
    
    return fig

# Define callback for stacked bar chart (deaths by gender and department)
@app.callback(
    Output('stacked-bar-graph', 'figure'),
    [Input('stacked-bar-graph', 'id')]
)
def update_stacked_bar_graph(id):
    if not data_loaded:
        return go.Figure().update_layout(title="No se pudieron cargar los datos de género")
    
    try:
        # Map sex codes to names
        sex_mapping = {
            1: 'Masculino',
            2: 'Femenino'
        }
        
        # Asegurarse de que el sexo sea numérico
        full_data['sexo'] = pd.to_numeric(full_data['sexo'], errors='coerce')
        full_data['sexo_nombre'] = full_data['sexo'].map(sex_mapping)
        
        # Manejar valores nulos o desconocidos
        full_data['sexo_nombre'] = full_data['sexo_nombre'].fillna('No especificado')
        
        # Calculate deaths by department and sex
        deaths_by_dept_sex = full_data.groupby(['departamento', 'sexo_nombre']).size().reset_index(name='total_muertes')
        
        # Eliminar departamentos sin nombre (si existen)
        deaths_by_dept_sex = deaths_by_dept_sex[deaths_by_dept_sex['departamento'].notna() & (deaths_by_dept_sex['departamento'] != '')]
        
        # Obtener top 15 departamentos por total de muertes para evitar gráfico sobrecargado
        top_depts = deaths_by_dept_sex.groupby('departamento')['total_muertes'].sum().nlargest(15).index.tolist()
        deaths_by_dept_sex = deaths_by_dept_sex[deaths_by_dept_sex['departamento'].isin(top_depts)]
        
        # Create stacked bar chart
        fig = px.bar(
            deaths_by_dept_sex,
            x='departamento',
            y='total_muertes',
            color='sexo_nombre',
            title='Comparación de Muertes por Sexo en los Principales Departamentos',
            labels={'total_muertes': 'Total Muertes', 'departamento': 'Departamento', 'sexo_nombre': 'Sexo'},
            color_discrete_map={
                'Masculino': '#3498db',
                'Femenino': '#e74c3c',
                'No especificado': '#95a5a6'
            }
        )
        
        fig.update_layout(
            height=600,
            xaxis_title='Departamento',
            yaxis_title='Total Muertes',
            legend_title='Sexo',
            barmode='stack',
            xaxis={'categoryorder':'total descending'}
        )
    except Exception as e:
        print(f"Error creating gender stacked bar chart: {e}")
        fig = go.Figure().update_layout(
            title="Error al crear el gráfico de muertes por sexo y departamento",
            height=600
        )
    
    return fig

if __name__ == '__main__':
    # For local development
    #app.run(debug=True)
    # For production deployment
    port = int(os.environ.get('PORT', 8000))  # Puerto por defecto 10000 si no hay variable de entorno PORT
    print(f"Iniciando servidor en el puerto {port}")
    server.run(host='0.0.0.0', port=port)