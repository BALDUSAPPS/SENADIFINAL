import streamlit as st
import fitz  # PyMuPDF
import re
from rapidfuzz import fuzz

# Configuración de la página
st.set_page_config(
    page_title="Buscador de Gacetas SENADI - Baldus Corp",
    page_icon="🔍",
    layout="wide"
)

def normalizar_fonetica(texto):
    """ Convierte una denominación a su representación fonética simplificada en español """
    texto = texto.upper().strip()
    texto = re.sub(r'[^A-ZÁÉÍÓÚÑ\s]', '', texto)
    
    replacements = [
        ('GE', 'JE'), ('GI', 'JI'), ('CIE', 'SIE'), ('CII', 'SII'),
        ('CE', 'SE'), ('CI', 'SI'), ('ZA', 'SA'), ('ZO', 'SO'), ('ZU', 'SU'),
        ('V', 'B'), ('K', 'C'), ('QU', 'C'), ('X', 'S'), ('H', ''),
        ('LL', 'Y'), ('W', 'V')
    ]
    for orig, repl in replacements:
        texto = texto.replace(orig, repl)
        
    texto = re.sub(r'(.)\1+', r'\1', texto)
    return texto

def calcular_similitud_fonetica(marca_buscada, marca_encontrada):
    """ Calcula el % de coincidencia fonética usando rapidfuzz """
    fon_buscada = normalizar_fonetica(marca_buscada)
    fon_encontrada = normalizar_fonetica(marca_encontrada)
    return round(fuzz.ratio(fon_buscada, fon_encontrada), 2)

def buscar_pagina_indice(doc):
    """ Localiza la página inicial del Índice de Signos Distintivos """
    for i in range(len(doc)):
        texto = doc[i].get_text("text").upper()
        if "ÍNDICE DE SIGNOS DISTINTIVOS" in texto or "INDICE DE SIGNOS DISTINTIVOS" in texto:
            return i
    return 0

def procesar_gaceta(pdf_bytes, marca_a_buscar, umbral_minimo):
    """ Procesa el PDF escaneando únicamente el índice """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    inicio_indice = buscar_pagina_indice(doc)
    resultados = []

    for num_pagina in range(inicio_indice, len(doc)):
        pagina = doc[num_pagina]
        texto = pagina.get_text("text")
        
        # Detiene la lectura si termina la sección del índice
        if "FIN DEL ÍNDICE" in texto.upper():
            break
            
        lineas = texto.split('\n')
        
        for linea in lineas:
            linea_limpia = linea.strip()
            
            # Filtrar vacíos o encabezados
            if not linea_limpia or any(h in linea_limpia.upper() for h in ["DENOMINACIÓN", "CLASE", "TRÁMITE", "SOLICITANTE"]):
                continue
            
            # Extraer solo la columna DENOMINACIÓN omitiendo la Clase Niza y el número de trámite
            match = re.match(r'^(.*?)(?:\s+\d{1,2})?\s+\d{4}-\d+.*$', linea_limpia)
            denominacion = match.group(1).strip() if match else linea_limpia
            
            if len(denominacion) < 2:
                continue

            # Cotejo fonético
            porcentaje_fonetico = calcular_similitud_fonetica(marca_a_buscar, denominacion)
            
            if porcentaje_fonetico >= umbral_minimo:
                resultados.append({
                    "Denominación Encontrada": denominacion,
                    "% Similitud Fonética": f"{porcentaje_fonetico}%",
                    "Página": num_pagina + 1,
                    "Score": porcentaje_fonetico
                })

    # Ordenar por mayor porcentaje
    resultados = sorted(resultados, key=lambda x: x["Score"], reverse=True)
    return resultados

# Interfaz Streamlit
st.title("🔍 Análisis de Marcas y Similitud Fonética - SENADI")
st.subheader("Búsqueda optimizada por Índice de Signos Distintivos")

st.sidebar.header("Parámetros de Búsqueda")
marca_ingresada = st.sidebar.text_input("Marca a evaluar:", placeholder="Ej. BALDUS")
umbral = st.sidebar.slider("Umbral mínimo de Similitud Fonética (%)", min_value=50, max_value=100, value=65, step=5)

uploaded_file = st.sidebar.file_uploader("Cargar Gaceta del SENADI (PDF)", type=["pdf"])

if st.sidebar.button("Iniciar Cotejo Fonético"):
    if not uploaded_file:
        st.error("Por favor, carga el archivo PDF de la Gaceta.")
    elif not marca_ingresada:
        st.error("Por favor, ingresa el nombre de la marca a evaluar.")
    else:
        with st.spinner("Escaneando el Índice de Signos Distintivos..."):
            bytes_data = uploaded_file.read()
            hallazgos = procesar_gaceta(bytes_data, marca_ingresada, umbral)
            
            if hallazgos:
                st.success(f"Se encontraron {len(hallazgos)} marcas con similitud fonética igual o superior al {umbral}%.")
                
                tabla_limpia = [{
                    "Denominación Encontrada": item["Denominación Encontrada"],
                    "% Similitud Fonética": item["% Similitud Fonética"],
                    "Página": item["Página"]
                } for item in hallazgos]
                
                st.dataframe(tabla_limpia, use_container_width=True)
            else:
                st.info(f"No se registraron marcas con similitud fonética superior al {umbral}% en el Índice.")
