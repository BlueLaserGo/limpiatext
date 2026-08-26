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

# 1. Configuracion de pagina
st.set_page_config(
    page_title="LimpiaText — Limpieza y traduccion de textos de pantalla",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Carga de avatar en Base64 con fallback
def obtener_imagen_base64(ruta_imagen):
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as img_file:
            return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode()}"
    return "https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg"

avatar_src = obtener_imagen_base64("avatar_lasergo.jpeg")

# 3. Estilo editorial minimalista (CSS en cadena segura)
css_styles = (
    "<style>\n"
    "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');\n"
    ".block-container { padding-top: 4.5rem !important; padding-bottom: 2rem !important; }\n"
    ".stApp { background-color: #EFEFEF; color: #111111; font-family: 'Inter', sans-serif; }\n"
    "section[data-testid='stSidebar'] { background-color: #E8E8E6; border-right: 1px solid #D5D5D0; }\n"
    ".hero-title { font-family: 'Space Grotesk', sans-serif; font-size: 2.1rem; font-weight: 700; letter-spacing: -1px; text-transform: uppercase; line-height: 1.1; color: #111111; margin-top: 0.4rem; margin-bottom: 0.2rem; }\n"
    ".hero-subtitle { font-size: 0.95rem; color: #555555; line-height: 1.4; max-width: 800px; margin-bottom: 1rem; }\n"
    ".stTabs [data-baseweb='tab-list'] { gap: 1.5rem; border-bottom: 1px solid #CCCCCC; }\n"
    ".stTabs [data-baseweb='tab'] { font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; font-size: 0.9rem !important; color: #111111 !important; }\n"
    "div[data-testid='stFileUploader'] { background-color: #FFFFFF !important; border: 2px dashed #FACC15 !important; border-radius: 6px !important; padding: 0.8rem !important; }\n"
    "div[data-testid='stFileUploader'] section button { background-color: #111111 !important; border: 1px solid #111111 !important; border-radius: 4px !important; padding: 0.35rem 1rem !important; transition: all 0.2s ease !important; }\n"
    "div[data-testid='stFileUploader'] section button * { display: none !important; }\n"
    "div[data-testid='stFileUploader'] section button::after { content: 'Examinar archivos'; font-family: 'Space Grotesk', sans-serif !important; font-size: 0.85rem !important; font-weight: 600 !important; color: #FFFFFF !important; }\n"
    "div[data-testid='stFileUploader'] section button:hover { background-color: #FACC15 !important; border-color: #FACC15 !important; }\n"
    "div[data-testid='stFileUploader'] section button:hover::after { color: #111111 !important; }\n"
    "div[data-testid='stFileUploaderInstructions'] * { display: none !important; }\n"
    "div[data-testid='stFileUploaderInstructions']::after { content: 'Max. 200 MB por archivo • Archivo CSV'; font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important; color: #666666 !important; display: inline-block; margin-left: 0.75rem; }\n"
    ".lang-item { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; font-size: 0.84rem; color: #111111; white-space: nowrap; }\n"
    ".lang-badge { background-color: #000000; color: #FFDE00; font-family: 'Space Grotesk', monospace; font-weight: 700; padding: 3px 6px; border-radius: 4px; font-size: 0.75rem; min-width: 28px; text-align: center; flex-shrink: 0; }\n"
    ".floating-card { background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 8px; padding: 1.4rem; box-shadow: 0 4px 10px rgba(0,0,0,0.04); transition: transform 0.2s ease, box-shadow 0.2s ease; margin-bottom: 1rem; }\n"
    ".floating-card:hover { transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: #BDBDB5; }\n"
    ".card-pill-yellow { display: inline-block; background-color: #FACC15; color: #111111; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.70rem; padding: 3px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem; }\n"
    ".card-pill-dark { display: inline-block; background-color: #111111; color: #FFDE00; font-family: 'Space Grotesk', monospace; font-weight: 700; font-size: 0.70rem; padding: 3px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem; }\n"
    ".card-heading { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05rem; color: #111111; margin-bottom: 0.6rem; }\n"
    ".stButton > button { background-color: #111111; color: #FFFFFF; border-radius: 4px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 0.95rem; letter-spacing: 0.5px; text-transform: uppercase; border: none; padding: 0.6rem 2.2rem; transition: all 0.2s ease; }\n"
    ".stButton > button:hover { background-color: #FACC15; color: #111111; }\n"
    "</style>"
)
st.markdown(css_styles, unsafe_allow_html=True)

# 4. Funciones de depuracion y soporte
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
    "Eres una analista funcional senior y especialista en localizacion linguistica de software.\n"
    "Tu tarea es analizar las Historias de Usuario (HDUs) de una aplicacion y extraer UNICAMENTE los textos visibles en pantalla que vera el usuario final:\n"
    "- Nombres de campos, botones, pestanas, titulos de formularios y selectores.\n"
    "- Mensajes de validacion, avisos, mensajes de error, modales o alertas.\n"
    "- Opciones de listas desplegables y titulos de seccion.\n\n"
    "NO extraigas descripciones explicativas, narrativa interna ni requisitos tecnicos. Extrae solo textos visibles para el usuario final.\n\n"
    "CRITERIOS DE CONFIANZA (0 a 100):\n"
    "- 90-100: Textos claramente visibles en pantalla (botones, titulos, mensajes, alertas, modales o textos explicitos).\n"
    "- 70-89: Textos probablemente visibles inferidos a partir del contexto de la historia.\n"
    "- 50-69: Textos ambiguos o cuya naturaleza visual en pantalla no es totalmente evidente.\n"
    "- 0-49: Textos que podrian ser notas internas, explicaciones tecnicas o logica de negocio no visible en pantalla.\n\n"
    "Para cada texto encontrado, devuelve obligatoriamente:\n"
    "1. id_hdu: El ID de la Historia de Usuario.\n"
    "2. modulo: El modulo funcional o area (ej. Facturacion, Clientes, Obras).\n"
    "3. pantalla: La vista o formulario dentro del modulo.\n"
    "4. tipo_elemento: Tipo de elemento (Boton, Campo, Mensaje de error, Alerta, Opcion desplegable, etc.).\n"
    "5. texto_es: El texto visible original en espanol.\n"
    "6. confianza: Numero entero entre 0 y 100 segun los criterios.\n"
    "7. traduccion_en: Traduccion al ingles.\n"
    "8. traduccion_ca: Traduccion al catalan / valenciano / balear.\n"
    "9. traduccion_gl: Traduccion al gallego.\n"
    "10. traduccion_eu:
