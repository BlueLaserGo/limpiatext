import streamlit as st
import pandas as pd
import json
import re
import html
import io
import os
import base64
from google import genai
from google.genai import types

# 1. Configuración de página
st.set_page_config(
    page_title="LimpiaText — Limpieza y traducción de textos de pantalla",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Carga de avatar en Base64 con fallback
def obtener_imagen_base64(ruta_imagen):
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as img_file:
            return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode()}"
    return "https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg"

avatar_src = obtener_imagen_base64("avatar_lasergo.jpeg")

# 3. Estilo editorial minimalista (CSS seguro)
css_styles = (
    "<style>\n"
    "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');\n"
    ".block-container { padding-top: 4.5rem !important; padding-bottom: 2rem !important; }\n"
    ".stApp { background-color: #EFEFEF; color: #111111; font-family: 'Inter', sans-serif; }\n"
    "section[data-testid='stSidebar'] { background-color: #E8E8E6; border-right: 1px solid #D5D5D0; }\n"
    "section[data-testid='stSidebar'] .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }\n"
    ".hero-title { font-family: 'Space Grotesk', sans-serif; font-size: 2.55rem; font-weight: 700; letter-spacing: -1.2px; text-transform: uppercase; line-height: 1.05; color: #111111; margin-top: 0.5rem; margin-bottom: 0.25rem; }\n"
    ".hero-subtitle { font-size: 0.96rem; color: #555555; line-height: 1.45; max-width: 820px; margin-bottom: 1.35rem; }\n"
    ".step-badge { display: inline-block; background-color: #111111; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.72rem; padding: 2px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.4rem; }\n"
    ".stTabs [data-baseweb='tab-list'] { gap: 1.5rem; border-bottom: 1px solid #CCCCCC; }\n"
    ".stTabs [data-baseweb='tab'] { font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; font-size: 0.9rem !important; color: #111111 !important; }\n"
    "div[data-testid='stFileUploader'] { background-color: #FFFFFF !important; border: 2px dashed #FACC15 !important; border-radius: 6px !important; padding: 0.8rem !important; }\n"
    "div[data-testid='stFileUploader'] section button { font-size: 0 !important; background-color: #111111 !important; color: transparent !important; border: 1px solid #111111 !important; border-radius: 4px !important; padding: 0.35rem 1rem !important; transition: all 0.2s ease !important; }\n"
    "div[data-testid='stFileUploader'] section button::after { content: 'Examinar archivos' !important; font-family: 'Space Grotesk', sans-serif !important; font-size: 0.85rem !important; font-weight: 600 !important; color: #FFFFFF !important; display: block !important; }\n"
    "div[data-testid='stFileUploader'] section button:hover { background-color: #FACC15 !important; border-color: #FACC15 !important; }\n"
    "div[data-testid='stFileUploader'] section button:hover::after { color: #111111 !important; }\n"
    "div[data-testid='stFileUploader'] section span { font-size: 0 !important; color: transparent !important; }\n"
    "div[data-testid='stFileUploader'] section span::after { content: 'o arrastra y suelta tu archivo aquí' !important; font-size: 0.85rem !important; color: #555555 !important; font-family: 'Inter', sans-serif !important; display: inline !important; }\n"
    "div[data-testid='stFileUploader'] section small { font-size: 0 !important; color: transparent !important; }\n"
    "div[data-testid='stFileUploader'] section small::after { content: '📄 Solo archivos CSV • Máximo 200 MB' !important; font-size: 0.80rem !important; color: #777777 !important; font-family: 'Inter', sans-serif !important; display: block !important; margin-top: 4px !important; }\n"
    ".lang-item { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 0.80rem; color: #222222; white-space: nowrap; }\n"
    ".lang-badge { background-color: #000000; color: #FFDE00; font-family: 'Space Grotesk', monospace; font-weight: 700; padding: 2px 5px; border-radius: 3px; font-size: 0.70rem; min-width: 24px; text-align: center; flex-shrink: 0; }\n"
    ".floating-card { background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 8px; padding: 1.4rem; box-shadow: 0 4px 10px rgba(0,0,0,0.04); transition: transform 0.2s ease, box-shadow 0.2s ease; margin-bottom: 1rem; }\n"
    ".floating-card:hover { transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: #BDBDB5; }\n"
    ".card-pill-yellow { display: inline-block; background-color: #FACC15; color: #111111; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.70rem; padding: 3px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem; }\n"
    ".card-pill-dark { display: inline-block; background-color: #111111; color: #FFDE00; font-family: 'Space Grotesk', monospace; font-weight: 700; font-size: 0.70rem; padding: 3px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem; }\n"
    ".card-heading { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05rem; color: #111111; margin-bottom: 0.6rem; }\n"
    ".stButton > button { background-color: #111111; color: #FFFFFF; border-radius: 4px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 0.95rem; letter-spacing: 0.5px; text-transform: uppercase; border: none; padding: 0.6rem 2.2rem; transition: all 0.2s ease; }\n"
    ".stButton > button:hover { background-color: #FACC15; color: #111111; }\n"
    "section[data-testid='stSidebar'] .stButton > button { padding: 0.3rem 0.6rem !important; font-size: 0.75rem !important; font-weight: 600 !important; text-transform: none !important; letter-spacing: 0 !important; background-color: #FFFFFF !important; color: #222222 !important; border: 1px solid #CCCCCC !important; box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important; margin-top: 0.2rem !important; margin-bottom: 0.4rem !important; }\n"
    "section[data-testid='stSidebar'] .stButton > button:hover { background-color: #FACC15 !important; border-color: #EAB308 !important; color: #111111 !important; }\n"
    "section[data-testid='stSidebar'] hr { margin-top: 0.6rem !important; margin-bottom: 0.6rem !important; }\n"
    "</style>"
)
st.markdown(css_styles, unsafe_allow_html=True)

# 4. Funciones de depuración y soporte
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

SYSTEM_PROMPT = (
    "Eres una analista funcional senior y especialista en localizacion linguistica de software. "
    "Tu tarea es analizar las Historias de Usuario (HDUs) de una aplicacion y extraer UNICAMENTE los textos visibles en pantalla que vera el usuario final: "
    "Nombres de campos, botones, pestanas, titulos de formularios, selectores, mensajes de validacion, avisos, errores, modales y opciones de listas. "
    "NO extraigas descripciones explicativas ni requisitos tecnicos. "
    "CRITERIOS DE CONFIANZA (0 a 100): "
    "90-100: Textos claramente visibles en pantalla (botones, titulos, mensajes, alertas). "
    "70-89: Textos probablemente visibles inferidos a partir del contexto funcional. "
    "50-69: Textos ambiguos cuya naturaleza visual no es totalmente evidente. "
    "0-49: Textos tecnicos o logica interna no visible para el usuario final. "
    "Para cada texto devuelve los campos: id_hdu, modulo, pantalla, tipo_elemento, texto_es, confianza (numero entero 0-100), "
    "traduccion_en, traduccion_ca, traduccion_gl, traduccion_eu. "
    "Responde EXCLUSIVAMENTE con una lista JSON valida de objetos."
)

# Definición de la ventana modal
@st.dialog("Ficha de proyecto — LimpiaText")
def mostrar_ficha():
    st.markdown(
        "### Propósito\n"
        "Herramienta concebida para analistas funcionales y equipos de localización.\n\n"
        "### Flujo de trabajo\n"
        "1. **Depuración:** Limpieza de marcado HTML y comentarios en exportaciones CSV de Azure DevOps.\n"
        "2. **Extracción:** Identificación de botones, campos y mensajes con índice de confianza IA (0–100).\n"
        "3. **Localización:** Traducción inmediata a 4 idiomas (EN, CA, GL, EU) descargable en Excel y CSV.\n\n"
        "### Requisitos de uso\n"
        "• **Modo Demo:** Funciona al instante sin necesidad de configuración.\n"
        "• **Archivos propios:** Requiere introducir una clave API gratuita de Gemini (Google AI Studio) en la barra lateral para asegurar la privacidad."
    )

# 5. Barra lateral (Sidebar)
with st.sidebar:
    sidebar_header_html = (
        "<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 0.4rem; padding-bottom: 0.4rem; border-bottom: 1px solid #D5D5D0;'>"
        f"<img src='{avatar_src}' style='width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid #CCCCCC; flex-shrink: 0;'>"
        "<div style='line-height: 1.15;'>"
        "<div style='font-size: 0.60rem; text-transform: uppercase; letter-spacing: 0.4px; color: #777777; font-weight: 600;'>Desarrollado por</div>"
        "<div style='font-size: 0.80rem; font-weight: 700; color: #111111;'>Laura Serrano Gómez</div>"
        "<a href='[https://www.linkedin.com/in/lauserrano](https://www.linkedin.com/in/lauserrano)' target='_blank' style='font-size: 0.68rem; color: #0066CC; text-decoration: none; font-weight: 500;'>Conectar en LinkedIn &#8599;</a>"
        "</div>"
        "</div>"
    )
    st.markdown(sidebar_header_html, unsafe_allow_html=True)

    if st.button("Información del proyecto", use_container_width=True):
        mostrar_ficha()

    api_key_env = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets else ""
    
    with st.expander("🔑 Configuración de API key", expanded=False):
        api_key_input = st.text_input(
            "Clave Gemini API:",
            value="",
            type="password",
            help="Opcional. Si se deja en blanco, la aplicación usará la clave preconfigurada del entorno."
        )
    
    api_key_activa = api_key_input.strip() if api_key_input.strip() else api_key_env

    st.markdown("<div style='font-size: 0.82rem; font-weight: 700; margin-top: 0.4rem;'>Fuente de datos:</div>", unsafe_allow_html=True)
    modo_entrada = st.radio(
        "Selecciona el origen:",
        ["Cargar archivo CSV", "Usar datos de demo (Azure DevOps)"],
