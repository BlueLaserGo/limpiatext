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
    initial__state="expanded"
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
    "section[data-testid='st'] { background-color: #E8E8E6; border-right: 1px solid #D5D5D0; }\n"
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

# 5. Barra lateral (Sidebar)
with st.sidebar:
    sidebar_header_html = (
        "<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 0.8rem; padding-bottom: 0.6rem; border-bottom: 1px solid #D5D5D0;'>"
        f"<img src='{avatar_src}' style='width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 1px solid #CCCCCC; flex-shrink: 0;'>"
        "<div style='line-height: 1.2;'>"
        "<div style='font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.5px; color: #666666; font-weight: 600;'>Desarrollado por</div>"
        "<div style='font-size: 0.88rem; font-weight: 700; color: #111111;'>Laura Serrano Gómez</div>"
        "<a href='https://www.linkedin.com/in/lauserrano' target='_blank' style='font-size: 0.72rem; color: #0066CC; text-decoration: none; font-weight: 500;'>Conectar en LinkedIn &#8599;</a>"
        "</div>"
        "</div>"
    )
    st.markdown(sidebar_header_html, unsafe_allow_html=True)

    api_key_env = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets else ""
    
    with st.expander("🔑 Configuración de API key", expanded=False):
        api_key_input = st.text_input(
            "Clave Gemini API:",
            value="",
            type="password",
            help="Opcional. Si se deja en blanco, la aplicacion usara la clave preconfigurada del entorno."
        )
    
    api_key_activa = api_key_input.strip() if api_key_input.strip() else api_key_env

    st.markdown("**Fuente de datos:**")
    modo_entrada = st.radio(
        "Selecciona el origen:",
        ["Cargar archivo CSV", "Usar datos de demo (Azure DevOps)"],
        label_visibility="collapsed"
    )

    st.write("---")

    _langs_html = (
        "<div style='margin-top: 6px;'>"
        "<div class='lang-item'><span class='lang-badge'>EN</span> Inglés</div>"
        "<div class='lang-item'><span class='lang-badge'>CA</span> Catalán / Valenciano / Balear</div>"
        "<div class='lang-item'><span class='lang-badge'>GL</span> Gallego</div>"
        "<div class='lang-item'><span class='lang-badge'>EU</span> Euskera</div>"
        "</div>"
    )
    st.markdown("**Idiomas de exportación:**")
    st.markdown(_langs_html, unsafe_allow_html=True)

# 6. Encabezado principal
hero_html = (
    "<div style='display: inline-block; background-color: #FACC15; color: #111111; font-family: \"Space Grotesk\", sans-serif; font-weight: 700; font-size: 0.72rem; padding: 4px 10px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px;'>"
    "Extracción y traducción de textos de pantalla"
    "</div>"
    "<div class='hero-title'>LimpiaText</div>"
    "<div class='hero-subtitle'>"
    "Detección automática de botones, campos y mensajes desde historias de <b>Azure DevOps</b>, "
    "limpieza de código HTML y traducción directa a 4 idiomas."
    "</div>"
)
st.markdown(hero_html, unsafe_allow_html=True)

# 7. Pestañas de contenido
tab_app, tab_guia = st.tabs(["🚀 Extraer y traducir textos", "📖 Guía de uso y preguntas frecuentes"])

with tab_app:
    df_devops = None

    if modo_entrada == "Cargar archivo CSV":
        archivo_subido = st.file_uploader(
            "Carga el CSV exportado de Azure DevOps",
            type=["csv"]
        )
        if archivo_subido:
            try:
                df_devops = pd.read_csv(archivo_subido, sep=None, engine='python')
                st.success(f"Archivo cargado con éxito: **{len(df_devops)}** historias de usuario detectadas.")
            except Exception as e:
                st.error(f"Error al leer el archivo CSV: {e}")
    else:
        st.info("📦 **Modo demo activado:** utilizando historias de usuario de ejemplo con código HTML para probar la aplicación.")
        datos_demo = {
            "ID": [1042, 1043, 1045],
            "Title": [
                "Gestión de facturas proforma",
                "Alta de nuevo proveedor comunitario",
                "Modificación de estado de expediente"
            ],
            "Description": [
                "<div>El usuario accederá a la pestaña <b>Facturación emitida</b> y pulsará el botón <i>Guardar borrador</i>.</div>",
                "<p>Formulario con selectores de tipo de IVA: <span>Exento</span>, <span>General 21%</span> y campo <b>NIF intracomunitario</b>.</p>",
                "<!-- Comentario interno: revisar permisos --><div>Si el expediente está bloqueado se mostrará el mensaje modal: <b>El expediente no admite modificaciones en estado Liquidado</b>.</div>"
            ],
            "Acceptance Criteria": [
                "<div>Criterio 1: El botón <b>Emitir factura definitiva</b> solo se habilitará tras validar el NIF. Aviso de éxito: <i>Factura registrada correctamente</i>.</div>",
                "<p>Criterio 2: Al pulsar <b>Cancelar registro</b> se solicita confirmación con la alerta: <i>¿Desea descartar los cambios no guardados?</i>.</p>",
                "<div>Criterio 3: Mensaje de error de validación: <b>Debe adjuntar al menos un justificante de pago</b>.</div>"
            ]
        }
        df_devops = pd.DataFrame(datos_demo)

    if df_devops is not None:
        with st.expander("Vista previa de las historias de usuario", expanded=(modo_entrada != "Cargar archivo CSV")):
            st.dataframe(df_devops.head(5), use_container_width=True)
            
        if st.button("Limpiar y traducir textos"):
            if not api_key_activa:
                st.error("Introduce tu clave Gemini API en la barra lateral para continuar.")
            else:
                with st.spinner("Limpiando etiquetas HTML y organizando campos..."):
                    col_id = obtener_columna(df_devops, ["ID", "Id", "Work Item Id"], 0)
                    col_title = obtener_columna(df_devops, ["Title", "Título"], 1)
                    col_desc = obtener_columna(df_devops, ["Description", "Descripción"], 2)
                    col_ac = obtener_columna(df_devops, ["Acceptance Criteria", "Criterios de Aceptación"], 3)
                    
                    df_devops["Description_Clean"] = df_devops[col_desc].apply(limpiar_html_devops) if col_desc else ""
                    df_devops["Acceptance_Criteria_Clean"] = df_devops[col_ac].apply(limpiar_html_devops) if col_ac else ""
                    
                    df_devops["Full_HDU_Text"] = (
                        "HDU ID: " + df_devops[col_id].astype(str) + "\n" +
                        "Título: " + df_devops[col_title].astype(str) + "\n" +
                        "Descripción: " + df_devops["Description_Clean"] + "\n" +
                        "Criterios de Aceptación: " + df_devops["Acceptance_Criteria_Clean"]
                    )
                    texto_completo_hdus = "\n\n---\n\n".join(df_devops["Full_HDU_Text"].tolist())

                with st.spinner("Identificando textos visibles y generando traducciones con IA..."):
                    client = genai.Client(api_key=api_key_activa)
                    prompt_usuario = (
                        "A continuación tienes el conjunto de Historias de Usuario para procesar:\n\n"
                        f"{texto_completo_hdus}\n\n"
                        "Extrae todos los textos de UI, calcula el índice de confianza (0-100), clasifícalos y tradúcelos según las directrices."
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_usuario,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    
                    try:
                        resultado_json = parsear_json_robusto(response.text)
                    except Exception:
                        st.error("La IA no devolvió un formato JSON válido.")
                        st.code(response.text)
                        st.stop()

                with st.spinner("Preparando tabla de resultados y exportaciones..."):
                    df_literales = pd.DataFrame(resultado_json)
                    
                    if 'confianza' in df_literales.columns:
                        df_literales['estado'] = df_literales['confianza'].apply(clasificar_confianza)
                    else:
                        df_literales['confianza'] = 90
                        df_literales['estado'] = "🟢 Alta"
                    
                    columnas_renombradas = {
                        'id_hdu': 'ID Historia',
                        'modulo': 'Módulo',
                        'pantalla': 'Pantalla / Formulario',
                        'tipo_elemento': 'Tipo de elemento',
                        'texto_es': 'Texto en pantalla (ES)',
                        'confianza': 'Confianza IA',
                        'estado': 'Estado',
                        'traduccion_en': 'Inglés (EN)',
                        'traduccion_ca': 'Catalán / Valenciano (CA)',
                        'traduccion_gl': 'Gallego (GL)',
                        'traduccion_eu': 'Euskera (EU)'
                    }
                    df_literales = df_literales.rename(columns=columnas_renombradas)
                    
                    orden_cols = [
                        'ID Historia', 'Módulo', 'Pantalla / Formulario', 'Tipo de elemento',
                        'Texto en pantalla (ES)', 'Confianza IA', 'Estado',
                        'Inglés (EN)', 'Catalán / Valenciano (CA)', 'Gallego (GL)', 'Euskera (EU)'
                    ]
                    cols_existentes = [c for c in orden_cols if c in df_literales.columns]
                    df_literales = df_literales[cols_existentes]

                    output_excel = io.BytesIO()
                    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                        df_literales.to_excel(writer, index=False, sheet_name='Textos UI')
                    excel_data = output_excel.getvalue()

                    csv_data = df_literales.to_csv(index=False, sep=";").encode('utf-8-sig')

                st.write("---")
                st.subheader("Textos identificados y traducidos")
                st.dataframe(df_literales, use_container_width=True)
                
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="Descargar en Excel (.xlsx)",
                        data=excel_data,
                        file_name="Textos_Pantalla_LimpiaText.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                with col_dl2:
                    st.download_button(
                        label="Descargar en CSV (.csv)",
                        data=csv_data,
                        file_name="Textos_Pantalla_LimpiaText.csv",
                        mime="text/csv"
                    )
