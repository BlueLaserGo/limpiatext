import streamlit as st
import pandas as pd
import json
import re
import html
import io
import os
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

    # Gestión de API Key: Automática por entorno con opción a meter una propia
    api_key_env = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets else ""
    
    with st.expander("🔑 Configuración de API Key", expanded=False):
        api_key_input = st.text_input(
            "Gemini API Key:",
            value="",
            type="password",
            help="Opcional. Si se deja en blanco, la aplicación usará la clave preconfigurada del entorno."
        )
    
    api_key_activa = api_key_input.strip() if api_key_input.strip() else api_key_env

    st.write("---")

    st.markdown("**Fuente de Datos:**")
    modo_entrada = st.radio(
        "Selecciona el origen:",
        ["Cargar archivo CSV", "Usar datos de Demo (Azure DevOps)"],
        label_visibility="collapsed"
    )

    st.write("---")

    st.markdown("**Idiomas de exportación:**")
    st.markdown("""
    <div style="margin-top: 8px;">
        <div class="lang-item"><span class="lang-badge">EN</span> Inglés</div>
        <div class="lang-item"><span class="lang-badge">CA</span> Catalán / Valenciano / Balear</div>
        <div class="lang-item"><span class="lang-badge">GL</span> Gallego</div>
        <div class="lang-item"><span class="lang-badge">EU</span> Euskera</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")
    
    # Autoría en el pie del sidebar
    col_perfil_img, col_perfil_text = st.columns([1, 3], gap="small")
    with col_perfil_img:
        if os.path.exists("avatar_lasergo.jpeg"):
            st.image("avatar_lasergo.jpeg", width=42)
        else:
            st.markdown("👤")
    with col_perfil_text:
        st.markdown("""
        <div style="line-height: 1.15; margin-top: 4px;">
            <div style="font-size: 0.80rem; font-weight: 700; color: #111111;">Laura Serrano Gómez</div>
            <a href="[https://www.linkedin.com/in/lauraserranogomez/](https://www.linkedin.com/in/lauraserranogomez/)" target="_blank" style="font-size: 0.70rem; color: #0066CC; text-decoration: none; font-weight: 500;">Conectar en LinkedIn ↗</a>
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
    df_devops = None

    if modo_entrada == "Cargar archivo CSV":
        archivo_subido = st.file_uploader(
            "Carga el CSV exportado de Azure DevOps (separador ';')",
            type=["csv"]
        )
        if archivo_subido:
            try:
                df_devops = pd.read_csv(archivo_subido, sep=";")
                st.success(f"Archivo cargado con éxito: **{len(df_devops)}** Historias de Usuario detectadas.")
            except Exception as e:
                st.error(f"Error al leer el archivo CSV: {e}")
    else:
        st.info("📦 **Modo Demo activado:** Utilizando conjunto de datos representativo de Azure DevOps con marcado HTML residual.")
        datos_demo = {
            "ID": [1042, 1043, 1045],
            "Title": [
                "Gestión de Facturas Proforma",
                "Alta de Nuevo Proveedor Comunitario",
                "Modificación de Estado de Expediente"
            ],
            "Description": [
                "<div>El usuario accederá a la pestaña <b>Facturación Emitida</b> y pulsará el botón <i>Guardar Borrador</i>.</div>",
                "<p>Formulario con selectores de tipo de IVA: <span>Exento</span>, <span>General 21%</span> y campo <b>NIF Intracomunitario</b>.</p>",
                "<!-- Comentario interno: revisar permisos --><div>Si el expediente está bloqueado se mostrará el mensaje modal: <b>El expediente no admite modificaciones en estado Liquidado</b>.</div>"
            ],
            "Acceptance Criteria": [
                "<div>Criterio 1: El botón <b>Emitir Factura Definitiva</b> solo se habilitará tras validar el NIF. Toast de éxito: <i>Factura registrada correctamente</i>.</div>",
                "<p>Criterio 2: Al pulsar <b>Cancelar Registro</b> se solicita confirmación con la alerta: <i>¿Desea descartar los cambios no guardados?</i>.</p>",
                "<div>Criterio 3: Mensaje de error de validación: <b>Debe adjuntar al menos un justificante de pago</b>.</div>"
            ]
        }
        df_devops = pd.DataFrame(datos_demo)

    if df_devops is not None:
        with st.expander("Vista previa de Historias de Usuario a procesar", expanded=(modo_entrada != "Cargar archivo CSV")):
            st.dataframe(df_devops.head(5), use_container_width=True)
            
        if st.button("Limpiar y Traducir Literales"):
            if not api_key_activa:
                st.error("Introduce tu Gemini API Key en la barra lateral para continuar.")
            else:
                with st.spinner("Limpiando HTML y normalizando campos..."):
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

                with st.spinner("Extrayendo literales con Gemini y analizando confianza..."):
                    client = genai.Client(api_key=api_key_activa)
                    prompt_usuario = (
                        "A continuación tienes el conjunto de Historias de Usuario para procesar:\n\n"
                        f"{texto_completo_hdus}\n\n"
                        "Extrae todos los literales de UI, calcula el índice de confianza (0-100), clasifícalos y tradúcelos según las directrices."
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
                        st.error("Gemini no devolvió un formato JSON válido.")
                        st.code(response.text)
                        st.stop()

                with st.spinner("Estructurando catálogo final con métricas de confianza..."):
                    df_literales = pd.DataFrame(resultado_json)
                    
                    if 'confianza' in df_literales.columns:
                        df_literales['estado'] = df_literales['confianza'].apply(clasificar_confianza)
                    else:
                        df_literales['confianza'] = 90
                        df_literales['estado'] = "🟢 Alta"
                    
                    columnas_renombradas = {
                        'id_hdu': 'ID HDU',
                        'modulo': 'Módulo Funcional',
                        'pantalla': 'Pantalla / Vista',
                        'tipo_elemento': 'Tipo de Elemento',
                        'texto_es': 'Literal (ES)',
                        'confianza': 'Confianza IA',
                        'estado': 'Estado',
                        'traduccion_en': 'Inglés (EN)',
                        'traduccion_ca': 'Catalán / Valenciano (CA)',
                        'traduccion_gl': 'Gallego (GL)',
                        'traduccion_eu': 'Euskera (EU)'
                    }
                    df_literales = df_literales.rename(columns=columnas_renombradas)
                    
                    orden_cols = [
                        'ID HDU', 'Módulo Funcional', 'Pantalla / Vista', 'Tipo de Elemento',
                        'Literal (ES)', 'Confianza IA', 'Estado',
                        'Inglés (EN)', 'Catalán / Valenciano (CA)', 'Gallego (GL)', 'Euskera (EU)'
                    ]
                    cols_existentes = [c for c in orden_cols if c in df_literales.columns]
                    df_literales = df_literales[cols_existentes]

                    output_excel = io.BytesIO()
                    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                        df_literales.to_excel(writer, index=False, sheet_name='Catálogo UI')
                    excel_data = output_excel.getvalue()

                    csv_data = df_literales.to_csv(index=False, sep=";").encode('utf-8-sig')

                st.write("---")
                st.subheader("Catálogo de UI con Métricas de Confianza")
                st.dataframe(df_literales, use_container_width=True)
                
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="Descargar Catálogo Excel (.xlsx)",
                        data=excel_data,
                        file_name="Catalogo_Literales_LimpiaText.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                with col_dl2:
                    st.download_button(
                        label="Descargar Catálogo CSV (.csv)",
                        data=csv_data,
                        file_name="Catalogo_Literales_LimpiaText.csv",
                        mime="text/csv"
                    )

with tab_guia:
    col_g1, col_g2 = st.columns(2, gap="medium")
    
    with col_g1:
        with st.container(border=True):
            st.markdown("**:orange[FLUJO FUNCIONAL]**")
            st.markdown("#### 🚀 Proceso en 4 Pasos")
            st.markdown("""
            1. **Origen de Datos:** Sube el CSV de Azure DevOps o activa el modo demo preconfigurado.
            2. **Depuración:** El algoritmo elimina marcado HTML (`<div>`, `<p>`) y comentarios.
            3. **Extracción & Scoring:** Aísla literales de UI y asigna el índice de fiabilidad (0–100).
            4. **Exportación:** Descarga el catálogo multilingüe en **Excel (.xlsx)** o **CSV**.
            """)

    with col_g2:
        with st.container(border=True):
            st.markdown("**:orange[CONTROL DE CALIDAD]**")
            st.markdown("#### 🎯 Métricas de Confianza IA")
            st.markdown("""
            * **🟢 Alta (≥ 85%):** Botones, modales, alertas y etiquetas visibles explícitas.
            * **🟡 Media (65% – 84%):** Literales inferidos a partir del contexto funcional.
            * **🔴 Revisar (< 65%):** Posibles reglas de negocio o textos técnicos a validar.
            """)

    with st.container(border=True):
        st.markdown("#### ❓ Preguntas Frecuentes (FAQ)")
        st.markdown("""
        **¿Por qué se descarta la prosa técnica larga?**  
        LimpiaText extrae exclusivamente los literales destinados a los archivos de localización de interfaz (UI), eliminando descripciones internas de arquitectura y reglas de negocio.

        **¿Qué idiomas incluye la exportación?**  
        Español original $\\rightarrow$ **Inglés (EN)**, **Catalán / Valenciano / Balear (CA)**, **Gallego (GL)** y **Euskera (EU)**.
        """)
