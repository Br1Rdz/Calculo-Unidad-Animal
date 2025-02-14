import streamlit as st 
from streamlit_folium import st_folium
import ee 
import geemap.foliumap as geemap
import folium
import pandas as pd
import plotly.express as px
import geemap.colormaps as cm
import datetime

#Credenciales de google earth engine
ee.Authenticate()
ee.Initialize(project='ee-brdzlopez')

#Configuracion de la pagina
st.set_page_config(page_title="Cálculo de unidades animales para pastoreo", 
                    page_icon="🐄", 
                   layout="wide",
                   initial_sidebar_state="auto",
                   menu_items=None)

markdown = """
    Cálculo de área idonea para el pastoreo apartir de imagenes LANDSAT 8.
    **Como funciona:**
    - Seleccion de píxeles con **NDVI idoneo**.
    - Calculo del área total en m².
    - Estimación de unidades animales para el predio.  
    \n
    Developed by Bruno Rodriguez
    """
#link de Contacto
url = "https://github.com/Br1Rdz/"

st.sidebar.title(":red-background[INFORMACION]\nV.1.0")
st.sidebar.info(markdown)
st.sidebar.info("Github: [Br1Rdz](%s)" % url)

logo = "./Clicker.jpg"
st.sidebar.image(logo)

st.title("📈 Cálculo de unidades animales")

# Fechas para ver diferentes cambios
with st.expander("🔧 Configuración de parámetros", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        Inicio = st.date_input("Fecha Inicial: YYYY/MM/DD", datetime.date(2024, 5, 1))
    with col2:
        Final = st.date_input("Fecha Final: YYYY/MM/DD", datetime.date(2024, 5, 31))
    Consumo_por_animal = st.number_input("Consumo por animal m²", value = 10.56)

#Cambio de formato
Fecha_inicio = Inicio.strftime("%Y-%m-%d")
Fecha_final = Final.strftime("%Y-%m-%d")

# Mapa interactivo
Map = geemap.Map(center=[23.634501, -102.552784], zoom=5, basemap="SATELLITE")

# Mostrar mapa
map_output = st_folium(Map, height=500, width=700)

if map_output and 'all_drawings' in map_output:
    if map_output['all_drawings']:
        geojson = map_output['all_drawings'][0]['geometry']
        predio = ee.Geometry(geojson)
        #Imagen Landsat 8
        image = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')\
            .filterBounds(predio)\
            .filterDate(Fecha_inicio, Fecha_final)\
            .sort("CLOUD_COVER")\
            .first()
        #Caluculo de NDVI
        def add_ee_layer(self, ee_image_object, vis_params, name):
                map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
                layer = folium.raster_layers.TileLayer(
                    tiles=map_id_dict['tile_fetcher'].url_format,
                    attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
                    name=name,
                    overlay=True,
                    control=True
                )
                layer.add_to(self)
                return layer

        # Add EE drawing method to folium.
        folium.Map.add_ee_layer = add_ee_layer
                
        NDVI = image.normalizedDifference(['SR_B5', 'SR_B4'])
        palette = cm.get_palette("ndvi", n_class = 8)
        vis_params = {"min": 0, "max": 1, "palette": palette}
        
        Map.add_ee_layer(NDVI.clip(predio), vis_params,'NDVI')
        
        #Extraccion de pixeles idoneos del NVDI
        zones = ee.Image(0).where(NDVI.gt(0.10), 1).unmask(0)
        area_idonea = zones.multiply(ee.Image.pixelArea())
        #Vectorixacion de Pixeles
        area_dict = area_idonea.reduceRegion(
            reducer = ee.Reducer.sum(),
            geometry = predio,
            scale = 30,
            maxPixels = 1e13
        )
        #Calculo de capacidad de carga
        area_m2 = area_dict.getInfo().get('constant', 0)
        estimacion_consumo = area_m2 / Consumo_por_animal
        st.markdown(f":gray-background[Para la fecha {image.get('DATE_ACQUIRED').getInfo()}, el área idónea fue de {area_m2:.2f} m², la cual soportar {estimacion_consumo:.2f} unidades animales.]")
    else:
        st.warning("Dibuja tu predio en el mapa antes de continuar.")
