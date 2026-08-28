import base64
import hashlib
import html
import io
import json
import os
import re

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y CONSTANTES
# ==========================================
st.set_page_config(
    page_title="LimpiaText — Limpieza y traducción de textos de pantalla",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MAX_HDUS_DEMO = 5
MAX_TAMANO_ARCHIVO_MB = 1
NOMBRES_COLUMNAS = {
    "id": ["ID", "Id", "Work Item Id", "Work Item ID"],
    "title": ["Title", "Título"],
    "description": ["Description", "Descripción"],
    "acceptance": [
        "Acceptance Criteria",
        "Criterios de Aceptación",
        "Criterios de aceptacion",
    ],
}
CARACTERES_FORMULA = ("=", "+", "-", "@")

# ==========================================
# 2. CARGA DE AVATAR (Base64 / Fallback)
# ==========================================
def obtener_imagen_base64(ruta_imagen):
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as img_file:
            contenido = base64.b64encode(img_file.read()).decode()
        return f"data:image/jpeg;base64,{contenido}"
    return "https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg"

avatar_src = obtener_imagen_base64("avatar_lasergo.jpeg")

# ==========================================
# 3. ESTILOS CSS (Editorial Minimalista)
# ==========================================
css_styles = """
<style>
:root {
    color-scheme: light !important;
}
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');
.block-container { padding-top: 4.5rem !important; padding-bottom: 2rem !important; }
.stApp { background-color: #EFEFEF !important; color: #111111 !important; font-family: 'Inter', sans-serif; }
section[data-testid='stSidebar'] { background-color: #E8E8E6 !important; border-right: 1px solid #D5D5D0; }
section[data-testid='stSidebar'] .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
.hero-title { font-family: 'Space Grotesk', sans-serif; font-size: 2.55rem; font-weight: 700; letter-spacing: -1.2px; text-transform: uppercase; line-height: 1.05; color: #111111; margin-top: 0.5rem; margin-bottom: 0.25rem; }
.hero-subtitle { font-size: 0.96rem; color: #555555; line-height: 1.45; max-width: 820px; margin-bottom: 1.35rem; }
.step-badge { display: inline-block; background-color: #111111; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.72rem; padding: 2px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.4rem; }
.stTabs [data-baseweb='tab-list'] { gap: 1.5rem; border-bottom: 1px solid #CCCCCC; }
.stTabs [data-baseweb='tab'] { font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; font-size: 0.9rem !important; color: #111111 !important; }
div[data-testid='stFileUploader'] { background-color: #FFFFFF !important; border: 2px dashed #FACC15 !important; border-radius: 6px !important; padding: 1rem !important; }
div[data-testid='stFileUploader'] button { font-size: 0 !important; background-color: #111111 !important; border: 1px solid #111111 !important; border-radius: 4px !important; padding: 0.4rem 1.2rem !important; transition: all 0.2s ease !important; }
div[data-testid='stFileUploader'] button * { display: none !important; }
div[data-testid='stFileUploader'] button::after { content: 'Examinar archivos' !important; font-family: 'Space Grotesk', sans-serif !important; font-size: 0.85rem !important; font-weight: 600 !important; color: #FFFFFF !important; display: block !important; }
div[data-testid='stFileUploader'] button:hover { background-color: #FACC15 !important; border-color: #FACC15 !important; }
div[data-testid='stFileUploader'] button:hover::after { color: #111111 !important; }
.lang-item { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 0.80rem; color: #222222; white-space: nowrap; }
.lang-badge { background-color: #000000; color: #FFDE00; font-family: 'Space Grotesk', monospace; font-weight: 700; padding: 2px 5px; border-radius: 3px; font-size: 0.70rem; min-width: 24px; text-align: center; flex-shrink: 0; }
.floating-card { background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 8px; padding: 1.4rem; box-shadow: 0 4px 10px rgba(0,0,0,0.04); transition: transform 0.2s ease, box-shadow 0.2s ease; margin-bottom: 1rem; }
.floating-card:hover { transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: #BDBDB5; }
.card-pill-yellow { display: inline-block; background-color: #FACC15; color: #111111; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.70rem; padding: 3px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem; }
.card-pill-dark { display: inline-block; background-color: #111111; color: #FFDE00; font-family: 'Space Grotesk', monospace; font-weight: 700; font-size: 0.70rem; padding: 3px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.6rem; }
.card-heading { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05rem; color: #111111; margin-bottom: 0.6rem; }
.stButton > button { background-color: #111111; color: #FFFFFF; border-radius: 4px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 0.95rem; letter-spacing: 0.5px; text-transform: uppercase; border: none; padding: 0.6rem 2.2rem; transition: all 0.2s ease; }
.stButton > button:hover { background-color: #FACC15; color: #111111; }
section[data-testid='stSidebar'] .stButton > button { padding: 0.3rem 0.6rem !important; font-size: 0.75rem !important; font-weight: 600 !important; text-transform: none !important; letter-spacing: 0 !important; background-color: #FFFFFF !important; color: #222222 !important; border: 1px solid #CCCCCC !important; box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important; margin-top: 0.2rem !important; margin-bottom: 0.4rem !important; }
section[data-testid='stSidebar'] .stButton > button:hover { background-color: #FACC15 !important; border-color: #EAB308 !important; color: #111111 !important; }
section[data-testid='stSidebar'] hr { margin-top: 0.6rem !important; margin-bottom: 0.6rem !important; }
</style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

# ==========================================
# 4. FUNCIONES DE PROCESAMIENTO Y SOPORTE
# ==========================================
def limpiar_html_devops(texto):
    if not isinstance(texto, str) or not texto.strip():
        return ""
    texto = html.unescape(texto)
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.DOTALL)
    texto = re.sub(r"<(br|/p|/div|/li|/tr|/h[1-6])\b[^>]*>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto)
    return texto.strip()

def obtener_columna(df, opciones_nombres):
    columnas_normalizadas = {
        str(columna).strip().casefold(): columna for columna in df.columns
    }
    for opcion in opciones_nombres:
        columna = columnas_normalizadas.get(opcion.strip().casefold())
        if columna:
            return columna
    return None

def clasificar_confianza(valor):
    try:
        valor = int(valor)
    except (ValueError, TypeError):
        return "🟡 Media"
    if valor >= 85:
        return "🟢 Alta"
    if valor >= 65:
        return "🟡 Media"
    return "🔴 Revisar"

def parsear_json_robusto(texto_respuesta):
    texto_limpio = texto_respuesta.strip()
    if texto_limpio.startswith("```"):
        texto_limpio = re.sub(r"^```[a-zA-Z]*\n?", "", texto_limpio)
        texto_limpio = re.sub(r"\n?```$", "", texto_limpio)
    coincidencia = re.search(r"\[\s*\{.*\}\s*\]", texto_limpio, re.DOTALL)
    if coincidencia:
        texto_limpio = coincidencia.group(0)
    resultado = json.loads(texto_limpio)
    if not isinstance(resultado, list):
        raise ValueError("La respuesta de IA no contiene una lista de elementos.")
    return resultado

def proteger_formula_excel(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor)
    if texto.startswith(CARACTERES_FORMULA):
        return "'" + texto
    return texto

def preparar_exportacion(df):
    df_exportacion = df.copy()
    for columna in df_exportacion.select_dtypes(include="object").columns:
        df_exportacion[columna] = df_exportacion[columna].map(proteger_formula_excel)
    return df_exportacion

def huella_archivo(archivo):
    contenido = archivo.getvalue()
    return hashlib.sha256(contenido).hexdigest()

def limpiar_resultado_si_cambia_origen(origen_actual, identificador_actual):
    origen_anterior = st.session_state.get("origen_anterior")
    identificador_anterior = st.session_state.get("identificador_archivo_anterior")
    if (
        origen_anterior is not None
        and (origen_anterior != origen_actual or identificador_anterior != identificador_actual)
    ):
        st.session_state.pop("df_resultado", None)
    st.session_state["origen_anterior"] = origen_actual
    st.session_state["identificador_archivo_anterior"] = identificador_actual

def validar_respuesta_ia(resultado_json, ids_hdu_validos):
    campos_obligatorios = {
        "id_hdu", "modulo", "pantalla", "tipo_elemento", "texto_es",
        "confianza", "traduccion_en", "traduccion_ca", "traduccion_gl", "traduccion_eu"
    }
