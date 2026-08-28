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

# 1. Configuración de página
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

# 2. Carga de avatar
def obtener_imagen_base64(ruta_imagen):
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as img_file:
            contenido = base64.b64encode(img_file.read()).decode()
        return f"data:image/jpeg;base64,{contenido}"
    return "https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg"

avatar_src = obtener_imagen_base64("avatar_lasergo.jpeg")

# 3. Estilos CSS
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

# 4. Funciones de soporte
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
    elementos_validos = []
    avisos = []

    for indice, elemento in enumerate(resultado_json, start=1):
        if not isinstance(elemento, dict):
            avisos.append(f"Elemento {indice}: formato no valido; se ha omitido.")
            continue

        faltantes = campos_obligatorios - set(elemento.keys())
        if faltantes:
            avisos.append(f"Elemento {indice}: faltan campos ({', '.join(sorted(faltantes))}); se ha omitido.")
            continue

        elemento["id_hdu"] = str(elemento["id_hdu"]).strip()
        if elemento["id_hdu"] not in ids_hdu_validos:
            avisos.append(f"Elemento {indice}: el ID '{elemento['id_hdu']}' no pertenece al archivo procesado; se ha omitido.")
            continue

        try:
            elemento["confianza"] = max(0, min(100, int(elemento["confianza"])))
        except (TypeError, ValueError):
            elemento["confianza"] = 50
            avisos.append(f"Elemento {indice}: confianza no valida; se ha establecido en 50.")

        elemento["texto_es"] = str(elemento["texto_es"]).strip()
        if not elemento["texto_es"]:
            avisos.append(f"Elemento {indice}: texto en espanol vacio; se ha omitido.")
            continue

        for campo in campos_obligatorios - {"confianza"}:
            elemento[campo] = str(elemento[campo]).strip()

        elementos_validos.append(elemento)

    if not elementos_validos:
        raise ValueError("No se ha recibido ningun elemento valido de la IA.")

    return elementos_validos, avisos

SYSTEM_PROMPT = (
    "Eres una analista funcional senior y especialista en localizacion linguistica de software. "
    "Analiza Historias de Usuario (HDUs) y extrae UNICAMENTE textos que vera el usuario final en la interfaz: "
    "nombres de campos, botones, pestanas, titulos de formularios, selectores, mensajes de validacion, "
    "avisos, errores, modales y opciones de listas. "
    "NO extraigas descripciones narrativas, requisitos tecnicos, logica interna, nombres de variables ni comentarios de desarrollo. "
    "Conserva sin modificar variables, placeholders, codigos, URLs, etiquetas HTML, Markdown, siglas y tokens como {0}, {nombre}, %s, {{user}} o {{count}}. "
    "Para modulo y pantalla, usa 'No indicado' cuando no este explicito. No inventes datos. "
    "Para tipo_elemento utiliza una categoria breve y concreta: Titulo, Etiqueta de campo, Boton, Pestana, Opcion de selector, "
    "Mensaje de exito, Mensaje de error, Mensaje de validacion, Modal de confirmacion, Texto de ayuda, Placeholder o Texto de tabla. "
    "CRITERIOS DE CONFIANZA (0 a 100): "
    "90-100: texto explicitamente visible en la HDU; 70-89: probablemente visible e inferido del contexto; "
    "50-69: ambiguo; 0-49: tecnico o no claramente visible. "
    "Devuelve para cada texto: id_hdu, modulo, pantalla, tipo_elemento, texto_es, confianza, traduccion_en, traduccion_ca, traduccion_gl, traduccion_eu. "
    "Responde EXCLUSIVAMENTE con una lista JSON valida de objetos."
)

# 5. Ventana modal
@st.dialog("Ficha de proyecto: LimpiaText")
def mostrar_ficha():
    ficha_html = """
    <div style='font-family: "Inter", sans-serif; color: #111111;'>
      <div style='margin-bottom: 1.2rem;'>
        <span class='card-pill-yellow'>Propósito</span>
        <div style='font-size: 0.92rem; line-height: 1.5; color: #333333; margin-top: 0.4rem;'>
          Herramienta diseñada para <b>analistas funcionales</b> y <b>equipos de localización</b> que necesitan extraer, validar y traducir textos de interfaz a partir de historias de usuario exportadas desde Azure DevOps.
        </div>
      </div>
      <div style='margin-bottom: 1.2rem;'>
        <span class='card-pill-dark'>Flujo de trabajo</span>
        <div style='background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 6px; padding: 0.9rem; margin-top: 0.4rem; font-size: 0.85rem; line-height: 1.6; color: #222222;'>
          <b>1. Depuración:</b> limpieza automática de marcado HTML y comentarios internos.<br>
          <b>2. Extracción IA:</b> detección de elementos visibles con cálculo de confianza (0–100).<br>
          <b>3. Localización:</b> generación de propuestas en 4 idiomas (EN, CA, GL, EU) listas para revisión humana.
        </div>
      </div>
      <div style='margin-bottom: 1rem;'>
        <span class='card-pill-yellow'>Modos de uso</span>
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 0.4rem;'>
          <div style='background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 6px; padding: 0.75rem; font-size: 0.82rem; line-height: 1.4;'>
            <b style='font-family: "Space Grotesk", sans-serif;'>📦 Modo Demo</b><br>
            <span style='color: #666666;'>Listo para probar al instante con ejemplos ficticios sin configurar clave API.</span>
          </div>
          <div style='background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 6px; padding: 0.75rem; font-size: 0.82rem; line-height: 1.4;'>
            <b style='font-family: "Space Grotesk", sans-serif;'>🔑 CSV Propio</b><br>
            <span style='color: #666666;'>Admite hasta 5 HDUs anonimizadas usando tu clave personal de Gemini API.</span>
          </div>
        </div>
      </div>
      <div style='font-size: 0.72rem; color: #777777; border-top: 1px solid #E0E0E0; padding-top: 0.6rem; margin-top: 0.8rem; text-align: right;'>
        Licencia: <a href='[https://github.com/BlueLaserGo/limpiatext/blob/main/License_LimpiaText.txt](https://github.com/BlueLaserGo/limpiatext/blob/main/License_LimpiaText.txt)' target='_blank' style='color: #111111; font-weight: 600; text-decoration: underline;'>MIT License</a> • © 2026 Laura Serrano Gómez
      </div>
    </div>
    """
    st.markdown(ficha_html, unsafe_allow_html=True)

# 6. Barra lateral
api_key_env = ""
try:
    api_key_env = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    api_key_env = ""

with st.sidebar:
    sidebar_header_html = f"""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 0.4rem; padding-bottom: 0.4rem; border-bottom: 1px solid #D5D5D0;'>
      <img src='{avatar_src}' style='width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid #CCCCCC; flex-shrink: 0;'>
      <div style='line-height: 1.15;'>
        <div style='font-size: 0.60rem; text-transform: uppercase; letter-spacing: 0.4px; color: #777777; font-weight: 600;'>Desarrollado por</div>
        <div style='font-size: 0.80rem; font-weight: 700; color: #111111;'>Laura Serrano Gómez</div>
        <a href='[https://www.linkedin.com/in/lauserrano](https://www.linkedin.com/in/lauserrano)' target='_blank' style='font-size: 0.68rem; color: #0066CC; text-decoration: none; font-weight: 500;'>Conectar en LinkedIn ↗</a>
      </div>
    </div>
    """
    st.markdown(sidebar_header_html, unsafe_allow_html=True)

    if st.button("Información del proyecto", use_container_width=True, key="boton_info"):
        mostrar_ficha()

    st.markdown("<div style='font-size: 0.82rem; font-weight: 700; margin-top: 0.4rem;'>Fuente de datos:</div>", unsafe_allow_html=True)
    modo_entrada = st.radio(
        "Selecciona el origen:",
        ["Usar datos de demo (Azure DevOps)", "Cargar archivo CSV propio"],
        label_visibility="collapsed",
        key="modo_entrada",
    )

    with st.expander("🔑 Clave Gemini API", expanded=False):
        api_key_input = st.text_input(
            "Clave personal de Gemini API",
            value="",
            type="password",
            key="api_key_input",
            help="Solo es necesaria para procesar un CSV propio. Se usa durante esta sesión y no se almacena.",
        )
        st.caption("El modo demo funciona con la clave preconfigurada. Para archivos propios usa tu clave personal.")

    st.markdown("<hr style='margin: 0.5rem 0; border: none; border-top: 1px solid #D5D5D0;'>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size: 0.82rem; font-weight: 700; margin-bottom: 4px;'>Idiomas de exportación:</div>"
        "<div class='lang-item'><span class='lang-badge'>EN</span> Inglés</div>"
        "<div class='lang-item'><span class='lang-badge'>CA</span> Catalán / Valenciano / Balear</div>"
        "<div class='lang-item'><span class='lang-badge'>GL</span> Gallego</div>"
        "<div class='lang-item'><span class='lang-badge'>EU</span> Euskera</div>",
        unsafe_allow_html=True,
    )

    sidebar_footer_html = """
    <div style='margin-top: 1.2rem; padding-top: 0.6rem; border-top: 1px solid #D5D5D0; text-align: center;'>
      <div style='font-size: 0.70rem; color: #333333; line-height: 1.4;'>
        Código abierto bajo <a href='[https://github.com/BlueLaserGo/limpiatext/blob/main/License_LimpiaText.txt](https://github.com/BlueLaserGo/limpiatext/blob/main/License_LimpiaText.txt)' target='_blank' style='color: #000000; font-weight: 700; text-decoration: underline;'>Licencia MIT</a><br>
        © 2026 Laura Serrano Gómez
      </div>
    </div>
    """
    st.markdown(sidebar_footer_html, unsafe_allow_html=True)

# 7. Encabezado principal
hero_html = """
<div style='display: inline-block; background-color: #FACC15; color: #111111; font-family: "Space Grotesk", sans-serif; font-weight: 700; font-size: 0.72rem; padding: 4px 10px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px;'>
  Extracción y traducción de textos de pantalla
</div>
<div class='hero-title'>LimpiaText</div>
<div class='hero-subtitle'>
  Sube Historias de Usuario exportadas desde <b>Azure DevOps</b>. LimpiaText elimina ruido técnico, detecta textos visibles de la aplicación y genera una propuesta de traducción para revisión humana antes de exportarla.
</div>
"""
st.markdown(hero_html, unsafe_allow_html=True)
st.info(
    "🎓 **Demo de portfolio.** Esta muestra ilustra un posible flujo de extracción y localización de textos UI. "
    "No es un entorno productivo y no debe utilizarse con información real, personal o confidencial."
)

plantilla_csv = """ID,Title,Description,Acceptance Criteria
1042,Gestión de facturas proforma,"El usuario accede a la pestaña <b>Facturación emitida</b>.","El botón <b>Guardar borrador</b> estará disponible."
1043,Alta de proveedor comunitario,"Formulario con el campo <b>NIF intracomunitario</b>.","Validar el NIF antes de guardar."
"""

# 8. Pestañas
tab_app, tab_guia = st.tabs(["🚀 Depura y traduce", "📖 Guía y ayuda"])

with tab_app:
    df_devops = None
    col_id = None
    col_title = None
    col_desc = None
    col_ac = None

    st.markdown("<div class='step-badge'>Paso 1</div>", unsafe_allow_html=True)
    st.markdown("#### Cargar historias de usuario")

    if modo_entrada == "Cargar archivo CSV propio":
        st.warning(
            f"**Uso de demostración:** carga únicamente ejemplos anonimizados y un máximo de {MAX_HDUS_DEMO} HDUs. "
            "No subas datos personales, información confidencial, credenciales, datos de clientes ni documentación interna."
        )
        st.caption(
            "Formato recomendado: una HDU por fila y las columnas `ID`, `Title`, `Description` y `Acceptance Criteria`. "
            "Son obligatorias `ID` y `Title`; debe existir al menos una columna de contenido: `Description` o `Acceptance Criteria`."
        )
        st.download_button(
            label="Descargar plantilla CSV de ejemplo",
            data=plantilla_csv.encode("utf-8-sig"),
            file_name="Plantilla_LimpiaText.csv",
            mime="text/csv",
            use_container_width=False,
            key="descargar_plantilla",
        )
        archivo_subido = st.file_uploader(
            "Carga el CSV exportado de Azure DevOps",
            type=["csv"],
            label_visibility="collapsed",
            key="archivo_csv",
        )

        if archivo_subido:
            limpiar_resultado_si_cambia_origen("csv", huella_archivo(archivo_subido))
            try:
                tamano_mb = archivo_subido.size / (1024 * 1024)
                if tamano_mb > MAX_TAMANO_ARCHIVO_MB:
                    st.error(f"El archivo supera el límite de {MAX_TAMANO_ARCHIVO_MB} MB establecido para esta demo.")
                    st.stop()

                df_devops = pd.read_csv(
                    archivo_subido,
                    sep=None,
                    engine="python",
                    dtype=str,
                    keep_default_na=False,
                )

                if df_devops.empty:
                    st.error("El CSV no contiene ninguna HDU.")
                    st.stop()

                if len(df_devops) > MAX_HDUS_DEMO:
                    st.error(
                        f"Esta demo admite un máximo de {MAX_HDUS_DEMO} HDUs por archivo. "
                        f"El archivo contiene {len(df_devops)} filas."
                    )
                    st.info("Reduce el CSV a las primeras 5 HDUs e inténtalo de nuevo.")
                    st.stop()

                col_id = obtener_columna(df_devops, NOMBRES_COLUMNAS["id"])
                col_title = obtener_columna(df_devops, NOMBRES_COLUMNAS["title"])
