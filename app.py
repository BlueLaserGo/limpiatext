import streamlit as st
import pandas as pd
import json
import re
import html
import io
from google import genai
from google.genai import types

# 1. Configuración de página
st.set_page_config(
    page_title="LimpiaText — UI Localization",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilo Editorial Minimalista (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 2rem !important;
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

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -1px;
        text-transform: uppercase;
        line-height: 1.1;
        color: #111111;
        margin-top: 0.4rem;
        margin-bottom: 0.2rem;
    }

    .hero-subtitle {
        font-size: 0.95rem;
        color: #555555;
        line-height: 1.4;
        max-width: 800px;
        margin-bottom: 1rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        border-bottom: 1px solid #CCCCCC;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        color: #111111 !important;
    }

    /* Caja del uploader con borde discontinuo amarillo */
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #FACC15 !important;
        border-radius: 6px !important;
        padding: 0.8rem !important;
    }

    /* Botón Uploader */
    div[data-testid="stFileUploader"] section button {
        background-color: #111111 !important;
        border: 1px solid #111111 !important;
        border-radius: 4px !important;
        padding: 0.35rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFileUploader"] section button * {
        display: none !important;
    }
    div[data-testid="stFileUploader"] section button::after {
        content: "Examinar archivos";
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stFileUploader"] section button:hover {
        background-color: #FACC15 !important;
        border-color: #FACC15 !important;
    }
    div[data-testid="stFileUploader"] section button:hover::after {
        color: #111111 !important;
    }

    div[data-testid="stFileUploaderInstructions"] * {
        display: none !important;
    }
    div[data-testid="stFileUploaderInstructions"]::after {
        content: "Máx. 200 MB por archivo • Archivo CSV";
        font-family: 'Inter', sans-serif !important;
        font-size: 0.82rem !important;
        color: #666666 !important;
        display: inline-block;
        margin-left: 0.75rem;
    }

    /* Badges de idiomas */
    .lang-item {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        font-size: 0.85rem;
        color: #111111;
        white-space: nowrap;
    }
    .lang-badge {
        background-color: #000000;
        color: #FFDE00;
        font-family: 'Space Grotesk', monospace;
        font-weight: 700;
        padding: 3px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        min-width: 28px;
        text-align: center;
        flex-shrink: 0;
    }

    .stButton > button {
        background-color: #111111;
        color: #FFFFFF;
        border-radius: 4px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border: none;
        padding: 0.6rem 2.2rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #FACC15;
        color: #111111;
    }
</style>
""", unsafe_allow_html=True)

# 3. Funciones de limpieza, soporte y robustez
def limpiar_html_devops(texto: str) -> str:
    if not isinstance(texto, str) or not texto.strip():
        return ""
    texto = html.unescape(texto)
    texto = re.sub(r'<!--.*?-->', '', texto, flags=re.DOTALL)
    texto = re.sub(r'<[^>]+>', '', texto)
    return re.sub(r'\s+', ' ', texto).strip()

def obtener_columna(df, opciones_nombres, indice_defecto=0):
    for col in df.columns:
        if col.strip().lower() in [op.lower() for op in opciones_nombres]:
            return col
    return df.columns[indice_defecto] if len(df.columns) > indice_defecto else None

def clasificar_confianza(valor):
    try:
        val = int(valor)
    except (ValueError, TypeError):
        return "🟡 Media"
    if val >= 85:
        return "🟢 Alta"
    elif val >= 65:
        return "🟡 Media"
    else:
        return "🔴 Revisar"

def parsear_json_robusto(texto_respuesta: str):
    texto_limpio = texto_respuesta.strip()
    if texto_limpio.startswith("```"):
        texto_limpio = re.sub(r'^```[a-zA-Z]*\n?', '', texto_limpio)
        texto_limpio = re.sub(r'\n?```$', '', texto_limpio)
    
    match = re.search(r'\[\s*\{.*\}\s*\]', texto_limpio, re.DOTALL)
    if match:
        texto_limpio = match.group(0)
        
    return json.loads(texto_limpio)

SYSTEM_PROMPT = """
Eres una analista funcional senior y especialista en localización de software multilingüe para el ámbito autonómico e internacional.
Tu tarea es analizar las Historias de Usuario (HDUs) de una iteración, una vez ya han sido refinadas, de una aplicación de software de gestión y extraer ÚNICAMENTE los literales que sean nuevos de interfaz (UI):
- Nombres de campos, botones, pestañas, títulos de nuevos formularios y ventanas, y selectores.
- Mensajes de validación, alertas, mensajes de error, modales o toasts.
- Opciones de menús desplegables y títulos de sección.

NO extraigas descripciones narrativas ni requisitos técnicos. Extrae solo textos visibles para el usuario final en la UI.

CRITERIOS DE ASIGNACIÓN DE CONFIANZA (0 a 100):
- 90-100: Textos claramente visibles en pantalla (botones, títulos, mensajes, alertas, modales o textos explícitos de UI en la HDU).
- 70-89: Textos probablemente visibles pero inferidos parcialmente a partir del contexto funcional.
- 50-69: Textos ambiguos o cuya naturaleza visual en pantalla no es completamente evidente.
- 0-49: Textos que podrían corresponder a reglas de negocio internas, explicaciones técnicas o contenido no visible para el usuario final.

Para cada literal encontrado, debes proporcionar obligatoriamente:
1. id_hdu: El ID de la Historia de Usuario correspondiente.
2. modulo: El área funcional o módulo (ej. Finanzas, Obras, Contabilidad).
3. pantalla: La vista o contexto dentro del módulo.
4. tipo_elemento: Tipo de elemento (Botón, Campo, Mensaje de error, Alerta, Opción desplegable, etc.).
5. texto_es: El literal original en español.
6. confianza: Número entero entre 0 y 100 según los criterios indicados.
7. traduccion_en: Traducción profesional al inglés.
8. traduccion_ca: Traducción profesional al catalán / valenciano / balear.
9. traduccion_gl: Traducción profesional al gallego.
10. traduccion_eu: Traducción profesional al euskera.

IMPORTANTE: Responde EXCLUSIVAMENTE con una lista JSON válida de objetos.
"""

# 4. Barra lateral (Sidebar)
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    api_key = st.text_input("Gemini API Key:", type="password", help="Introduce tu clave de API de Google Gemini.")

    st.write("---")

    st.markdown("**Idiomas de exportación:**")
    st.markdown("""
    <div style="margin-top: 10px;">
        <div class="lang-item"><span class="lang-badge">EN</span> Inglés</div>
        <div class="lang-item"><span class="lang-badge">CA</span> Catalán / Valenciano / Balear</div>
        <div class="lang-item"><span class="lang-badge">GL</span> Gallego</div>
        <div class="lang-item"><span class="lang-badge">EU</span> Euskera</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")
    
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-top: 1.5rem;">
        <img src="[https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg](https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg)" 
             style="width: 28px; height: 28px; border-radius: 50%; object-fit: cover; border: 1px solid #CCCCCC; flex-shrink: 0;">
        <div style="line-height: 1.15;">
            <div style="font-size: 0.76rem; font-weight: 600; color: #222222;">Laura Serrano Gómez</div>
            <a href="[https://www.linkedin.com/in/lauraserranogomez/](https://www.linkedin.com/in/lauraserranogomez/)" target="_blank" style="font-size: 0.68rem; color: #666666; text-decoration: none;">LinkedIn ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 5. Encabezado principal (Hero Editorial)
st.markdown("""
<div style="display: inline-block; background-color: #FACC15; color: #111111; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.72rem; padding: 4px 10px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px;">
    Extracción y traducción de literales
</div>
<div class="hero-title">LimpiaText</div>
<div class="hero-subtitle">
    Extracción inteligente de literales de interfaz desde exportaciones de <b>Azure DevOps</b>, 
    depuración de marcado HTML residual y catálogo de localización multilingüe inmediato.
</div>
""", unsafe_allow_html=True)

# 6. Pestañas de contenido
tab_app, tab_guia = st.tabs(["🚀 Procesar Literales", "📖 Guía de Usuario & FAQ"])

with tab_app:
    archivo_
