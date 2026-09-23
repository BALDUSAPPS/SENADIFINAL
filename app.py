import streamlit as st
import urllib.request
import pandas as pd
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
import re
import time
import os

# Configuración de la página
st.set_page_config(
    page_title="Cotejo de Gacetas SENADI",
    page_icon="⚖️",
    layout="wide"
)

# Estilo visual moderno y limpio
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 25px;
    }
    .creator-tag {
        font-size: 0.9rem;
        color: #2563EB;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# Lógica de Normalización y Similitud Fonética en Español
def normalizar_fonetica(texto):
    """ Convierte el texto a su representación fonética en español """
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

def calcular_similitud_fonetica(marca_buscada, texto_encontrado):
    """ Calcula el % de coincidencia fonética """
    fon_buscada = normalizar_fonetica(marca_buscada)
    fon_encontrada = normalizar_fonetica(texto_encontrado)
    return round(fuzz.ratio(fon_buscada, fon_encontrada), 2)

# Sidebar corporativa
with st.sidebar:
    st.image("https://img.icons8.com/color/96/law.png", width=80)
    st.markdown("### **Panel de Control**")
    st.markdown("Herramienta automatizada de vigilancia y cotejo fonético para propiedad intelectual.")
    
    umbral_fonetico = st.slider("Umbral mínimo de Similitud Fonética (%)", min_value=50, max_value=100, value=65, step=5)
    
    st.markdown("---")
    st.markdown("<p class='creator-tag'>Creado por BALDUS CORP</p>", unsafe_allow_html=True)
    st.markdown("© 2026 Todos los derechos reservados.")

# Interfaz Principal
st.markdown("<p class='main-header'>Vigilancia Inteligente de Gacetas SENADI</p>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Sube tu portafolio de marcas y procesa la Gaceta en tiempo real.</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Sube tu archivo Excel de marcas (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    df_excel = pd.read_excel(uploaded_file)
    
    # Detectar columna de marcas automáticamente
    columna_candidata = [c for c in df_excel.columns if 'denominacion' in c.lower() or 'marca' in c.lower()]
    if columna_candidata:
        columna_marcas = columna_candidata[0]
        st.success(f"Archivo cargado correctamente. Se detectó la columna: **{columna_marcas}**")
        
        gaceta_num = st.text_input("Número de Gaceta a analizar:", value="763")
        
        if st.button("Iniciar Cotejo de Marcas", type="primary"):
            df_excel['Marca_clean'] = df_excel[columna_marcas].astype(str).str.upper().str.strip()
            total_paginas = 1058
            hallazgos = []
            
            # Contenedores visuales para el progreso y el juego
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Pestañas para separar el proceso del entretenimiento
            tab_progreso, tab_juego = st.tabs(["📊 Estado del Proceso", "🎮 Zona Arcade (Minijuego)"])
            
            with tab_juego:
                st.markdown("### Disfruta mientras el sistema procesa el análisis masivo:")
                if os.path.exists("game.html"):
                    with open("game.html", "r", encoding="utf-8") as f:
                        html_game = f.read()
                    st.components.v1.html(html_game, height=450, scrolling=False)
                else:
                    st.info("Coloca el archivo game.html en el repositorio para activar el minijuego.")

            with tab_progreso:
                status_text.text("Buscando inicio del ÍNDICE DE SIGNOS DISTINTIVOS para acelerar el proceso...")
                
                # 1. Localizar la página donde inicia el Índice
                pagina_inicio_indice = 1
                for p_check in range(1, 150): # El índice suele estar en las primeras páginas
                    url_check = f"http://gaceta.propiedadintelectual.gob.ec:8180/Gacetas/{gaceta_num}/files/basic-html/page{p_check}.html"
                    try:
                        req = urllib.request.Request(url_check, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=2) as resp:
                            soup = BeautifulSoup(resp.read(), 'html.parser')
                            txt_check = soup.get_text().upper()
                            if "ÍNDICE DE SIGNOS DISTINTIVOS" in txt_check or "INDICE DE SIGNOS DISTINTIVOS" in txt_check:
                                pagina_inicio_indice = p_check
                                break
                    except:
                        continue
                
                # 2. Escaneo optimizado desde la página del Índice
                for p in range(pagina_inicio_indice, total_paginas + 1):
                    porcentaje = int(((p - pagina_inicio_indice + 1) / (total_paginas - pagina_inicio_indice + 1)) * 100)
                    progress_bar.progress(porcentaje)
                    status_text.text(f"Analizando Índice - Página {p} de {total_paginas} ({porcentaje}%)")
                    
                    url = f"http://gaceta.propiedadintelectual.gob.ec:8180/Gacetas/{gaceta_num}/files/basic-html/page{p}.html"
                    try:
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=2) as resp:
                            soup = BeautifulSoup(resp.read(), 'html.parser')
                            texto_pagina = soup.get_text().upper()
                            
                            # Si termina la sección del índice se puede cortar el bucle
                            if "FIN DEL ÍNDICE" in texto_pagina:
                                break

                            lineas = texto_pagina.split('\n')
                            
                            for linea in lineas:
                                linea_limpia = linea.strip()
                                
                                # Filtrar líneas vacías o encabezados de la tabla del índice
                                if not linea_limpia or any(h in linea_limpia for h in ["DENOMINACIÓN", "CLASE", "TRÁMITE", "SOLICITANTE"]):
                                    continue
                                
                                # Aislar únicamente la denominación ignorando la clase Niza y el trámite
                                match = re.match(r'^(.*?)(?:\s+\d{1,2})?\s+\d{4}-\d+.*$', linea_limpia)
                                denominacion_gaceta = match.group(1).strip() if match else linea_limpia
                                
                                if len(denominacion_gaceta) < 2:
                                    continue
                                
                                # Evaluar cotejo fonético con cada marca del Excel
                                for _, row in df_excel.iterrows():
                                    marca_usuario = row['Marca_clean']
                                    if len(marca_usuario) < 2:
                                        continue
                                    
                                    score_fonetico = calcular_similitud_fonetica(marca_usuario, denominacion_gaceta)
                                    
                                    if score_fonetico >= umbral_fonetico:
                                        hallazgos.append({
                                            "Página": p,
                                            "Tu Marca": row[columna_marcas],
                                            "Marca Encontrada en Gaceta": denominacion_gaceta,
                                            "% Similitud Fonética": f"{score_fonetico}%",
                                            "Score": score_fonetico
                                        })
                    except:
                        continue

                progress_bar.progress(100)
                status_text.text("¡Proceso de cotejo finalizado con éxito!")

                if hallazgos:
                    df_res = pd.DataFrame(hallazgos).drop_duplicates(subset=["Página", "Tu Marca", "Marca Encontrada en Gaceta"])
                    df_res = df_res.sort_values(by="Score", ascending=False).drop(columns=["Score"])
                    
                    st.balloons()
                    st.success(f"Se encontraron {len(df_res)} coincidencias fonéticas.")
                    
                    # Mostrar tabla de resultados en pantalla
                    st.dataframe(df_res, use_container_width=True)
                    
                    # Botón de descarga para el reporte en Excel
                    archivo_salida = f"Reporte_Gaceta_{gaceta_num}.xlsx"
                    df_res.to_excel(archivo_salida, index=False)
                    
                    with open(archivo_salida, "rb") as f:
                        st.download_button(
                            label="📥 Descargar Reporte en Excel",
                            data=f,
                            file_name=archivo_salida,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.warning("No se encontraron coincidencias fonéticas relevantes con las marcas de tu portafolio en esta gaceta.")
    else:
        st.error("El Excel subido no contiene una columna identificable con los nombres de las marcas ('Denominacion' o 'Marca').")
