import streamlit as st 
import geemap 
import ee 
# import os 
import geemap.foliumap as geemap
# import datetime
import pandas as pd
import plotly.express as px
import geemap.colormaps as cm
import json

# Cargar los secretos
json_data = st.secrets["json_data"]
service_account = st.secrets["service_account"]

# Authorising the app
credentials = ee.ServiceAccountCredentials(service_account, key_data = json_data)
ee.Initialize(credentials)

#Configuracion de la pagina
st.set_page_config(page_title="Cálculo de unidades animales para pastoreo", 
                    page_icon="📊", 
                   layout="wide",
                   initial_sidebar_state="auto",
                   menu_items=None)

markdown = """
    Calculo de area idonea para el pastoreo apartir de imagenes LANDSAT8.
    Como funciona:
    \n-Se seleccionan los píxeles donde idoneos del **NDVI**.
    \n-Se calcula el área total en m².
    \n-Se estima cuántas unidades animales puede soportar el predio  
    \n
    Developed 
    by Bruno Rodriguez
    """
#link de Contacto
url = "https://github.com/Br1Rdz/"

st.sidebar.title(":red-background[INFORMACION]\nV.1.0")
st.sidebar.info(markdown)
st.sidebar.info("Github: [Br1Rdz](%s)" % url)

logo = "./Clicker.jpg"
st.sidebar.image(logo)

st.markdown("<h1 style='text-align: center;'>Calculo de unidades animales para un predio.</h1>", unsafe_allow_html=True)


Map = geemap.Map(center = [25.587194, -103.518631], zoom = 15
                            , basemap='HYBRID', show=True) 

# poligono de extension
Sitio = ee.Geometry.Polygon([
                [[-103.528574, 25.592127],
                 [-103.526540, 25.578888],
                 [-103.508735, 25.579290],
                 [-103.507879, 25.594368]]
                ])


#Predio
plot_id = 'plot_id'

#Aqui se pueden agregar mas localidades
Predio = ee.FeatureCollection([
    #Chapala
    ee.Feature(ee.Geometry.Polygon([[
                                      [-103.520098,  25.583237],
                                      [-103.520474,  25.583398],
                                      [-103.520435,  25.586354],
                                      [-103.519400,  25.587736],
                                      [-103.515704,  25.588613],
                                      [-103.515295,  25.587590],
                                      [-103.518150,  25.586720],
                                      [-103.519172,  25.585462]]]), {plot_id: 1})])

#Fechas para ver diferentes cambios
Fecha_inicio = st.text_input("Fecha inicio", "2024-05-01")
Fecha_final = st.text_input("Fecha final", "2024-05-31")

#cargar las capas satelitales
image = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')\
            .filterBounds(Sitio) \
            .filterDate(f'{Fecha_inicio}', f'{Fecha_final}') \
            .sort("CLOUD_COVER") \
            .first()
          # .mean()

            
#NDVI
NDVI = image.normalizedDifference(['SR_B5', 'SR_B4'])

vis = {"min": 0, "max": 1, "palette": "ndvi"}

palette = cm.get_palette("ndvi", n_class = 2)

# Map.addLayer(Predio, {}, 'Predio')

# Map.addLayer(NDVI.clip(Sitio),
#             #  {'min': 0, 'max': 1, 'palette':['black', 'yellow','green']},
#             {'min': 0, 'max': 1, 'palette':palette},
#              'NDVI',True, 0.60)

# Map.add_colorbar(vis, label="NDVI")

# Map.addLayer(Predio, {}, 'Predio')

# Map.to_streamlit(height = 600)

#Transformar resultado a imagen
mapa = ee.Image(NDVI)

# Obtener la región de estudio (Predio)
region = mapa.geometry().bounds()
subset = mapa.clip(Predio)

# Clasificar áreas idóneas
zones = (ee.Image(0)  # Imagen base con valores 0 (no idóneo)
         .where(subset.gt(0.10), 1)  # NDVI > 0.10 → Clase 1 (idóneo)
         .unmask(0))

area_idonea = zones.multiply(ee.Image.pixelArea())

# Reducir la región para obtener el área total en m²
area_dict = area_idonea.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=Predio,  # Asegurar que el cálculo se hace dentro del Predio
    scale=30,  # Ajusta según la resolución de la imagen (Sentinel-2: 10m, Landsat: 30m)
    maxPixels=1e13
)

#NDVI
mapa = ee.Image(NDVI)
# Obtener la región de estudio (Predio)
region = mapa.geometry().bounds()
subset = mapa.clip(Predio)

# Clasificar áreas idóneas
zones = (ee.Image(0)  # Imagen base con valores 0 (no idóneo)
         .where(subset.gt(0.10), 1)  # NDVI > 0.10 → Clase 1 (idóneo)
         .unmask(0))

area_idonea = zones.multiply(ee.Image.pixelArea())

# Reducir la región para obtener el área total en m²
area_dict = area_idonea.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=Predio,  # Asegurar que el cálculo se hace dentro del Predio
    scale=30,  # Ajusta según la resolución de la imagen (Sentinel-2: 10m, Landsat: 30m)
    maxPixels=1e13
)

# Obtener el resultado en metros cuadrados
area_m2 = area_dict.getInfo()
# print(f"Área idónea en m²: {area_m2['constant']:.2f}") 

#Calculo de consumo por unidad animal
# Unidades_animales = st.text_input("Unidades animales", "5")
Consumo_por_animal = st.text_input("Consumo animal en m²", "10.56")
#Resultado de area idonea
# st.markdown(f":gray-background[Área idónea en m²: {area_m2['constant']:.2f}]")

Estimacion_consumo = area_m2['constant'] / float(Consumo_por_animal)

st.markdown(f":gray-background[Para la fecha {image.get('DATE_ACQUIRED').getInfo()}, el área idónea fue de {area_m2['constant']:.2f} m², la cual soportar {Estimacion_consumo:.2f} unidades animales.]")

#Visualizacion del predio
Map.addLayer(NDVI.clip(Sitio),
            #  {'min': 0, 'max': 1, 'palette':['black', 'yellow','green']},
            {'min': 0, 'max': 1, 'palette':palette},
             'NDVI',True, 0.60)

Map.add_colorbar(vis, label="NDVI")

Map.addLayer(Predio, {}, 'Predio')

Map.to_streamlit(height = 600)

############################################################################

# NDVI_predio = geemap.zonal_stats(mapa,
#                                 Predio,
#                                 "NDVI_stats.csv",
#                                 statistics_type = "MEAN", scale = 1,
#                                 return_fc=True, verbose=False) #Esto es para guardar en el objeto

# #Tranformacion a dataframe
# temp_df = geemap.ee_to_df(NDVI_predio)

# #Renombrar columnas
# temp_df2 = temp_df.rename(columns={"plot_id":"Predio","mean":"NDVI"})
# #asignacion de los valores de la tabla a ala colonia
# # temp_df2.replace(to_replace={1:"Plaza Corazón",2:"Plaza el Dorado",3:"Filadelfia",4:"Nucleo universitario"},inplace=True)

# #plot del grafico de temperaturas
# fig = px.bar(temp_df2, 
#              x='Predio', 
#              y='NDVI', 
#              color="Predio",
#             #  labels={
#             #          "Colonia": "Plaza",
#             #          "Temperatura": "Temperatura (°C)",
#             #          "Colonias": "Colonia" #Esta es de leyenda
#             #      },
#              width=600,
#              height=400,
#              title="NDVI_predio"
#              )

# #Actualizaciones al plot
# fig.update_layout(showlegend=False)
# #https://stackoverflow.com/questions/76910223/how-to-reduce-the-decimal-places-in-a-bar-chart-created-by-plotly-express

# fig.update_layout(
#     xaxis_title_text="Sitios de Gómez Palacio, Dgo.", 
# ) 

# fig.update_traces(
#     marker_line_width = 0, 
#     texttemplate = "%{value:.2f}"
# ) 

# #Visualizacion del grafico
# st.plotly_chart(fig, theme=None, use_container_width=True)
