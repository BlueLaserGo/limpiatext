import streamlit as st
import pandas as pd
import json
import io
import os
from google import genai
from google.genai import types

from utils import PROMPT_EXTRACCION, PROMPT_TRADUCCION, limpiar_html_devops, obtener_columna

# 1. Configuración de página
st.set_page_config(
    page_title="LimpiaText — Preparación y traducción de textos de UI",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilos CSS Compactos y Editoriales
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px;
    }

    .stApp {
        background-color: #EFEFEF;
        color: #111111;
        font-family: 'Inter', sans-serif;
    }

    section[data-testid="stSidebar"] {
        background-color: #E8E8E6;
        border-right: 1px solid #D5D5D0;
    }

    .hero-tag {
        display: inline-block;
        background-color: #FACC15;
        color: #111111;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 0.72rem;
        padding: 3px 8px;
        border-radius: 3px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -1px;
        text-transform: uppercase;
        line-height: 1.05;
        color: #111111;
        margin: 0.2rem 0;
    }

    .hero-subtitle {
        font-size: 0.95rem;
        color: #444444;
        line-height: 1.45;
        margin-bottom: 1.4rem;
    }

    .step-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.05rem;
        font-weight: 700;
        color: #111111;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 1rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .step-badge {
        background-color: #111111;
        color: #FACC15;
        font-size: 0.75rem;
        padding: 2px 6px;
        border-radius: 3px;
    }

    .human-loop-banner {
        background-color: #FFFFFF;
        border-left: 4px solid #FACC15;
        padding: 0.6rem 1rem;
        border-radius: 0 4px 4px 0;
        margin-bottom: 0.8rem;
        font-size: 0.86rem;
        color: #333333;
    }

    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.2rem;
        border-bottom: 1px solid #CCCCCC;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: #111111 !important;
        padding: 0.4rem 0.2rem !important;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #FACC15 !important;
        color: #000000 !important;
    }

    /* Uploader */
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #FACC15 !important;
        border-radius: 6px !important;
        padding: 0.6rem 0.8rem !important;
    }

    div[data-testid="stFileUploader"] section > button {
        background-color: #111111 !important;
        border: 1px solid #111111 !important;
        border-radius: 4px !important;
        padding: 0.35rem 1rem !important;
    }
    div[data-testid="stFileUploader"] section > button * { display: none !important; }
    div[data-testid="stFileUploader"] section > button::after {
        content: "Examinar archivos";
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stFileUploaderInstructions"] > div:first-child { display: none !important; }
    div[data-testid="stFileUploaderInstructions"]::after {
        content: "Máx. 200 MB • CSV";
        font-size: 0.8rem !important;
        color: #666666 !important;
        margin-left: 0.5rem;
    }

    div[data-testid="stFileUploaderFileData"] button { background: transparent !important; border: none !important; }
    div[data-testid="stFileUploaderFileData"] button::after { content: "" !important; }

    /* Badges de idiomas */
    .lang-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        font-size: 0.82rem;
        color: #111111;
    }
    .lang-badge {
        background-color: #000000;
        color: #FFDE00;
        font-family: 'Space Grotesk', monospace;
        font-weight: 700;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 0.72rem;
        min-width: 26px;
        text-align: center;
    }

    /* Botones compactos y equilibrados */
    .stButton > button, div[data-testid="stDownloadButton"] > button {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.3px !important;
        text-transform: none !important;      /* Evita mayúsculas forzadas que ensanchan el botón */
        border: none !important;
        padding: 0.35rem 0.9rem !important;   /* Reduce altura y márgenes laterales */
        min-height: 2.2rem !important;        /* Altura estándar y compacta */
        line-height: 1.2 !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover {
        background-color: #FACC15 !important;
        color: #111111 !important;
    }
    /* Tarjetas del manual */
    .guide-card {
        background-color: #FFFFFF;
        border: 1px solid #D5D5D0;
        border-radius: 6px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .guide-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        border-color: #CCCCCC;
    }
    .guide-card h4 {
        margin: 0 0 0.4rem 0;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.95rem;
        font-weight: 700;
    }
    .guide-card p, .guide-card li {
        font-size: 0.86rem;
        color: #444444;
        line-height: 1.45;
    }
</style>
""", unsafe_allow_html=True)

# 3. Datos de ejemplo para demo
EJEMPLO_CSV = """ID;Title;Description;Acceptance Criteria
1042;Formulario de Alta de Expedientes;<div><p>Como tramitador quiero dar de alta un nuevo expediente.</p></div>;<div><ul><li>El botón debe ser <b>Guardar borrador</b> y <b>Enviar a revisión</b>.</li><li>Si falta el NIF mostrar: <i>El NIF introducido no es válido o está incompleto</i>.</li><li>El selector de estado tendrá: <i>Pendiente</i>, <i>En trámite</i> y <i>Resuelto</i>.</li></ul></div>
1043;Gestión de Notificaciones de Usuario;<div><p>Configuración de avisos por correo y SMS.</p></div>;<div><ul><li>Título de ventana: <b>Preferencias de Notificación</b>.</li><li>Pestaña: <b>Canales directos</b>.</li><li>Checkbox: <b>Recibir alertas urgentes vía SMS</b>.</li><li>Modal de confirmación: <b>¿Desea aplicar los cambios en sus suscripciones activas?</b></li></ul></div>
1044;Buscador Avanzado de Facturas;<div><p>Filtros por rango de fecha e importe.</p></div>;<div><ul><li>Etiquetas de campo: <b>Fecha desde</b> y <b>Fecha hasta</b>.</li><li>Botón de acción: <b>Exportar listado</b>.</li><li>Alerta si no hay datos: <b>No se han encontrado facturas para el periodo seleccionado</b>.</li></ul></div>
"""

# 4. Barra lateral y diálogo informativo
@st.dialog("👀 ¿De qué va este proyecto?")
def ver_ficha_proyecto():
    st.markdown("""
    ### LimpiaText
    **Autora:** Laura Serrano Gómez  
    **Propósito:** Ejercicio práctico para automatizar la extracción de textos de interfaz a partir de historias de usuario y prepararlos para traducción.

    * **⚙️ 01. Limpieza con reglas:** Elimina etiquetas HTML y ruido residual de los datos.
    * **🤖 02. Identificación con IA:** Detecta qué textos son botones, mensajes o campos mediante Gemini 3.6 Flash.
    * **👩‍💻 03. Revisión humana:** Permite editar los textos directamente en pantalla antes de traducir.
    * **🌍 04. Traducción multilingüe:** Genera versiones en **EN**, **CA**, **GL** y **EU**.
    * **💾 05. Exportación:** Descarga en formato **Excel (.xlsx)** o **CSV (.csv)**.
    """)
    st.write("---")

    ruta_pdf = "Ficha_Proyecto_LimpiaText_LauraSerrano.pdf"
    if os.path.exists(ruta_pdf):
        with open(ruta_pdf, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="⬇ Descargar Ficha Técnica en PDF",
            data=pdf_bytes,
            file_name="LimpiaText_Ficha_Proyecto.pdf",
            mime="application/pdf",
            use_container_width=True
        )

with st.sidebar:
    default_api_key = st.secrets.get("GEMINI_API_KEY", "")
    
    if default_api_key:
        st.success("🟢 Motor de IA conectado")
        with st.expander("⚙️ Configuración de API Key"):
            api_key = st.text_input("Gemini API Key:", value=default_api_key, type="password")
    else:
        api_key = st.text_input("Gemini API Key:", value="", type="password", help="Introduce tu API Key de Google AI Studio.")

    st.write("---")

    st.markdown("**Idiomas disponibles:**")
    st.markdown("""
    <div>
        <div class="lang-item"><span class="lang-badge">EN</span> Inglés</div>
        <div class="lang-item"><span class="lang-badge">CA</span> Catalán / Valenciano / Balear</div>
        <div class="lang-item"><span class="lang-badge">GL</span> Gallego</div>
        <div class="lang-item"><span class="lang-badge">EU</span> Euskera</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")

    st.markdown("**Documentación:**")
    if st.button("👀 ¿De qué va este proyecto?", use_container_width=True):
        ver_ficha_proyecto()

    st.markdown("""
    <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #D5D5D0; display: flex; align-items: center; gap: 8px;">
        <img src="https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg" 
             style="width: 28px; height: 28px; border-radius: 50%; object-fit: cover; border: 1px solid #CCCCCC; flex-shrink: 0;">
        <div style="line-height: 1.15;">
            <div style="font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.5px; color: #666666; font-weight: 600;">Desarrollado por</div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #222222;">Laura Serrano Gómez</div>
            <a href="https://www.linkedin.com/in/lauserrano/" target="_blank" 
               style="font-size: 0.70rem; color: #666666; text-decoration: none;">LinkedIn ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 5. Encabezado principal
st.markdown("""
<div class="hero-tag">Proyecto de Portfolio · Ejercicio Práctico</div>
<div class="hero-title">LimpiaText</div>
<div class="hero-subtitle">
    Encuentra y prepara los textos que aparecen en tu aplicación.<br>
    Limpia el código residual, identifica botones y mensajes visibles, permite revisarlos y genera versiones en varios idiomas.
</div>
""", unsafe_allow_html=True)

# Estado de sesión
if "df_devops" not in st.session_state:
    st.session_state.df_devops = None
if "df_literales" not in st.session_state:
    st.session_state.df_literales = None
if "traducido" not in st.session_state:
    st.session_state.traducido = False

# 6. Pestañas
tab_app, tab_guia = st.tabs(["🚀 Preparar Textos", "📖 Cómo Funciona el Proyecto"])

with tab_app:
    st.markdown('<div class="step-header"><span class="step-badge">01</span> Añade tus historias de usuario</div>', unsafe_allow_html=True)
    
    # Proporciones equilibradas para los botones de acción
    col_demo1, col_demo2, col_reset = st.columns([1.6, 1.4, 1.1])
    with col_demo1:
        if st.button("📁 Probar con datos de ejemplo", use_container_width=True):
            st.session_state.df_devops = pd.read_csv(io.StringIO(EJEMPLO_CSV), sep=";")
            st.session_state.df_literales = None
            st.session_state.traducido = False
            st.rerun()

    with col_demo2:
        st.download_button(
            label="⬇ Descargar muestra",
            data=EJEMPLO_CSV.encode("utf-8-sig"),
            file_name="Export_DevOps_Sprint42_Sample.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_reset:
        if st.button("🔄 Limpiar datos", use_container_width=True):
            st.session_state.df_devops = None
            st.session_state.df_literales = None
            st.session_state.traducido = False
            st.rerun()

    archivo_subido = st.file_uploader(
        "O sube tu propio archivo CSV exportado de Azure DevOps:",
        type=["csv"]
    )
with tab_guia:
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("""
        <div class="guide-card">
            <h4>⚙️ 1. Reglas y patrones (Regex)</h4>
            <p>Las exportaciones de Azure DevOps suelen contener marcado HTML residual (<code>&lt;div&gt;</code>, <code>&lt;ul&gt;</code>, <code>&lt;b&gt;</code>). El motor aplica filtros deterministas para limpiar ese ruido antes de pasarlo a la IA.</p>
        </div>
        <div class="guide-card">
            <h4>🤖 2. IA para identificar y estructurar</h4>
            <p>Gemini analiza la descripción funcional para distinguir qué partes son explicaciones internas y qué partes corresponden a <b>botones, etiquetas, campos y alertas visibles</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_g2:
        st.markdown("""
        <div class="guide-card">
            <h4>👩‍💻 3. Revisión humana (Human-in-the-loop)</h4>
            <p>La IA propone una primera versión estructurada, pero el analista o lingüista mantiene el control total para editar, añadir o borrar textos antes de traducir.</p>
        </div>
        <div class="guide-card">
            <h4>🌍 4. Traducción y exportación</h4>
            <p>Genera versiones en cuatro lenguas y descarga el resultado en Excel o CSV listo para incorporar al desarrollo o a herramientas de traducción.</p>
        </div>
        """, unsafe_allow_html=True)
