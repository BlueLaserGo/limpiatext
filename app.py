import streamlit as st
import pandas as pd
import json
import io
from google import genai
from google.genai import types

from utils import PROMPT_EXTRACCION, PROMPT_TRADUCCION, limpiar_html_devops, obtener_columna

# 1. Configuración de página
st.set_page_config(
    page_title="LimpiaText — UI Localization",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilos CSS
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

    /* Caja del uploader */
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #FACC15 !important;
        border-radius: 6px !important;
        padding: 0.8rem !important;
    }

    /* Botón examinar archivos principal */
    div[data-testid="stFileUploader"] section > button {
        background-color: #111111 !important;
        border: 1px solid #111111 !important;
        border-radius: 4px !important;
        padding: 0.35rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFileUploader"] section > button * {
        display: none !important;
    }
    div[data-testid="stFileUploader"] section > button::after {
        content: "Examinar archivos";
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stFileUploader"] section > button:hover {
        background-color: #FACC15 !important;
        border-color: #FACC15 !important;
    }
    div[data-testid="stFileUploader"] section > button:hover::after {
        color: #111111 !important;
    }

    /* Ocultar texto nativo y evitar botones dobles */
    div[data-testid="stFileUploaderInstructions"] > div:first-child {
        display: none !important;
    }
    div[data-testid="stFileUploaderInstructions"]::after {
        content: "Máx. 200 MB por archivo • Archivo CSV";
        font-family: 'Inter', sans-serif !important;
        font-size: 0.82rem !important;
        color: #666666 !important;
        display: inline-block;
        margin-left: 0.5rem;
    }

    /* Botón de eliminar archivo cargado (icono papelera limpio) */
    div[data-testid="stFileUploaderFileData"] button {
        background: transparent !important;
        border: none !important;
    }
    div[data-testid="stFileUploaderFileData"] button::after {
        content: "" !important;
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

    /* Botones principales y de descarga */
    .stButton > button, div[data-testid="stDownloadButton"] > button {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        border: none !important;
        padding: 0.6rem 2.2rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover {
        background-color: #FACC15 !important;
        color: #111111 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Datos de ejemplo para demo
EJEMPLO_CSV = """ID;Title;Description;Acceptance Criteria
1042;Formulario de Alta de Expedientes;<div><p>Como tramitador quiero dar de alta un nuevo expediente.</p></div>;<div><ul><li>El botón debe ser <b>Guardar borrador</b> y <b>Enviar a revisión</b>.</li><li>Si falta el NIF mostrar: <i>El NIF introducido no es válido o está incompleto</i>.</li><li>El selector de estado tendrá: <i>Pendiente</i>, <i>En trámite</i> y <i>Resuelto</i>.</li></ul></div>
1043;Gestión de Notificaciones de Usuario;<div><p>Configuración de avisos por correo y SMS.</p></div>;<div><ul><li>Título de ventana: <b>Preferencias de Notificación</b>.</li><li>Pestaña: <b>Canales directos</b>.</li><li>Checkbox: <b>Recibir alertas urgentes vía SMS</b>.</li><li>Modal de confirmación: <b>¿Desea aplicar los cambios en sus suscripciones activas?</b></li></ul></div>
1044;Buscador Avanzado de Facturas;<div><p>Filtros por rango de fecha e importe.</p></div>;<div><ul><li>Etiquetas de campo: <b>Fecha desde</b> y <b>Fecha hasta</b>.</li><li>Botón de acción: <b>Exportar listado</b>.</li><li>Alerta si no hay datos: <b>No se han encontrado facturas para el periodo seleccionado</b>.</li></ul></div>
"""

# 4. Barra lateral
with st.sidebar:
    default_api_key = st.secrets.get("GEMINI_API_KEY", "")

    api_key = st.text_input(
        "Gemini API Key:",
        value=default_api_key,
        type="password",
        help="Clave para procesar con Gemini."
    )

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

    st.markdown("""
    <div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #D5D5D0; display: flex; align-items: center; gap: 8px;">
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
<div style="display: inline-block; background-color: #FACC15; color: #111111; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 0.72rem; padding: 4px 10px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px;">
    Extracción y traducción de literales
</div>
<div class="hero-title">LimpiaText</div>
<div class="hero-subtitle">
    Extracción inteligente de literales de interfaz desde exportaciones de <b>Azure DevOps</b>, 
    depuración de marcado HTML residual y catálogo de localización multilingüe inmediato.
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
tab_app, tab_guia = st.tabs(["🚀 Procesar Literales", "📖 Guía de Usuario & FAQ"])

with tab_app:
    archivo_subido = st.file_uploader(
        "Carga el CSV exportado de Azure DevOps",
        type=["csv"]
    )

    col_demo1, col_demo2 = st.columns([1.8, 1])
    with col_demo1:
        if st.button("📁 Cargar datos de prueba de ejemplo"):
            st.session_state.df_devops = pd.read_csv(io.StringIO(EJEMPLO_CSV), sep=";")
            st.session_state.df_literales = None
            st.session_state.traducido = False
    with col_demo2:
        st.download_button(
            label="⬇ Descargar CSV de ejemplo",
            data=EJEMPLO_CSV.encode("utf-8-sig"),
            file_name="Export_DevOps_Sprint42_Sample.csv",
            mime="text/csv"
        )

    if archivo_subido is not None:
        try:
            st.session_state.df_devops = pd.read_csv(archivo_subido, sep=None, engine='python', encoding='utf-8-sig')
            st.session_state.df_literales = None
            st.session_state.traducido = False
        except Exception as e:
            st.error(f"Error al leer el archivo subido: {e}")

    # Si hay datos cargados
    if st.session_state.df_devops is not None:
        df_act = st.session_state.df_devops
        st.success(f"Archivo listo: **{len(df_act)}** Historias de Usuario cargadas.")
        
        with st.expander("Vista previa del CSV original"):
            st.dataframe(df_act.head(3), use_container_width=True)
            
        # PASO 1: EXTRAER Y LIMPIAR
        if st.button("1. Extraer y Limpiar Literales (Español)"):
            if not api_key:
                st.error("Introduce tu Gemini API Key en la barra lateral para continuar.")
            else:
                with st.spinner("Limpiando marcado HTML y procesando HDUs con Gemini..."):
                    col_id = obtener_columna(df_act, ["ID", "Id", "Work Item Id", "Id de elemento de trabajo"], 0)
                    col_title = obtener_columna(df_act, ["Title", "Título"], 1)
                    col_desc = obtener_columna(df_act, ["Description", "Descripción"], 2)
                    col_ac = obtener_columna(df_act, ["Acceptance Criteria", "Criterios de Aceptación", "Criterios de aceptacion"], 3)
                    
                    df_act["Description_Clean"] = df_act[col_desc].apply(limpiar_html_devops) if col_desc else ""
                    df_act["Acceptance_Criteria_Clean"] = df_act[col_ac].apply(limpiar_html_devops) if col_ac else ""
                    
                    df_act["Full_HDU_Text"] = (
                        "HDU ID: " + df_act[col_id].astype(str) + "\n" +
                        "Título: " + df_act[col_title].astype(str) + "\n" +
                        "Descripción: " + df_act["Description_Clean"] + "\n" +
                        "Criterios de Aceptación: " + df_act["Acceptance_Criteria_Clean"]
                    )
                    texto_completo_hdus = "\n\n---\n\n".join(df_act["Full_HDU_Text"].tolist())

                    client = genai.Client(api_key=api_key)
                    prompt_usuario = f"Historias de Usuario:\n\n{texto_completo_hdus}\n\nExtrae únicamente los literales de interfaz en español."
                    
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt_usuario,
                        config=types.GenerateContentConfig(
                            system_instruction=PROMPT_EXTRACCION,
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    
                    try:
                        resultado_json = json.loads(response.text)
                        df_res = pd.DataFrame(resultado_json)
                        columnas_renombradas = {
                            'id_hdu': 'ID HDU',
                            'modulo': 'Módulo Funcional',
                            'pantalla': 'Pantalla / Vista',
                            'tipo_elemento': 'Tipo de Elemento',
                            'texto_es': 'Literal (ES)'
                        }
                        st.session_state.df_literales = df_res.rename(columns=columnas_renombradas)
                        st.session_state.traducido = False
                    except Exception:
                        st.error("Gemini no devolvió un formato JSON válido.")
                        st.code(response.text)

    # Si ya se extrajeron literales
    if st.session_state.df_literales is not None:
        st.write("---")
        st.subheader("Catálogo de UI (Editable)")
        st.caption("Revisa o edita la tabla antes de descargar o traducir.")
        
        df_editado = st.data_editor(
            st.session_state.df_literales,
            use_container_width=True,
            num_rows="dynamic"
        )
        st.session_state.df_literales = df_editado

        # PASO 2: TRADUCIR (OPCIONAL)
        if not st.session_state.traducido:
            st.write("")
            if st.button("2. Traducir Catálogo a Multilingüe (EN, CA, GL, EU)"):
                if not api_key:
                    st.error("Introduce tu Gemini API Key en la barra lateral para continuar.")
                else:
                    with st.spinner("Generando traducciones multilingües con Gemini..."):
                        datos_a_traducir = df_editado.to_dict(orient="records")
                        client = genai.Client(api_key=api_key)
                        prompt_traduccion = f"Literales a traducir:\n\n{json.dumps(datos_a_traducir, ensure_ascii=False)}"
                        
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=prompt_traduccion,
                            config=types.GenerateContentConfig(
                                system_instruction=PROMPT_TRADUCCION,
                                response_mime_type="application/json",
                                temperature=0.1
                            )
                        )
                        
                        try:
                            resultado_traducciones = json.loads(response.text)
                            df_trad = pd.DataFrame(resultado_traducciones)
                            columnas_renombradas = {
                                'id_hdu': 'ID HDU',
                                'modulo': 'Módulo Funcional',
                                'pantalla': 'Pantalla / Vista',
                                'tipo_elemento': 'Tipo de Elemento',
                                'texto_es': 'Literal (ES)',
                                'traduccion_en': 'Inglés (EN)',
                                'traduccion_ca': 'Catalán / Valenciano (CA)',
                                'traduccion_gl': 'Gallego (GL)',
                                'traduccion_eu': 'Euskera (EU)'
                            }
                            st.session_state.df_literales = df_trad.rename(columns=columnas_renombradas)
                            st.session_state.traducido = True
                            st.rerun()
                        except Exception:
                            st.error("Error al procesar las traducciones.")
                            st.code(response.text)

        # BLOQUE DE DESCARGA
        st.write("---")
        col_formato, col_boton = st.columns([1, 2])
        
        with col_formato:
            formato_descarga = st.selectbox(
                "Formato de exportación:",
                ["Excel (.xlsx)", "CSV (.csv)"]
            )
            
        with col_boton:
            st.write("")
            st.write("")
            if formato_descarga == "Excel (.xlsx)":
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df_editado.to_excel(writer, index=False, sheet_name='Catálogo UI')
                data_file = output_excel.getvalue()
                nombre_archivo = "Catalogo_Literales_LimpiaText.xlsx"
                tipo_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                data_file = df_editado.to_csv(index=False, sep=";").encode("utf-8-sig")
                nombre_archivo = "Catalogo_Literales_LimpiaText.csv"
                tipo_mime = "text/csv"

            st.download_button(
                label=f"Descargar Catálogo ({formato_descarga})",
                data=data_file,
                file_name=nombre_archivo,
                mime=tipo_mime
            )

with tab_guia:
    st.markdown("### 📘 Guía de Operación y Manual de Usuario")
    st.markdown("""
    **LimpiaText** automatiza la extracción de cadenas de texto de interfaz (UI) a partir de las Historias de Usuario refinadas en Azure DevOps, eliminando el marcado HTML residual y generando un catálogo estructurado multilingüe.
    """)
    
    st.write("---")
    
    st.markdown("**1. Extracción desde Azure DevOps**")
    st.markdown("""
    * Ve a **Boards > Queries** en tu proyecto de Azure DevOps.
    * Crea o abre una consulta con las HDUs de la iteración correspondiente.
    * Asegúrate de incluir en la vista las columnas mínimas: `ID`, `Title`, `Description` y `Acceptance Criteria`.
    * Pulsa en **Export to CSV** (detecta automáticamente delimitadores `,`, `;` o tabulador con codificación UTF-8).
    """)

    st.markdown("**2. Flujo de Trabajo en LimpiaText**")
    st.markdown("""
    * **Paso 1 (Extracción & Limpieza):** Sube tu archivo CSV (o usa los datos de prueba de ejemplo) y pulsa **1. Extraer y Limpiar Literales (Español)**.
    * **Edición interactiva:** Corrige erratas o añade términos directamente en la tabla editable.
    * **Paso 2 (Localización Multilingüe):** Pulsa **2. Traducir Catálogo** para generar las columnas en Inglés, Catalán/Valenciano/Balear, Gallego y Euskera.
    * **Exportación:** Elige formato Excel (`.xlsx`) o CSV (`.csv`) y descarga el catálogo listo para tu equipo.
    """)

    st.write("---")

    st.markdown("### ❓ Preguntas Frecuentes (FAQ)")
    
    with st.expander("¿Qué criterios sigue para ignorar texto técnico?"):
        st.write("""
        El motor analiza el contexto semántico de los Criterios de Aceptación y descarta descripciones de arquitectura, llamadas API o lógica interna de backend, capturando exclusivamente textos que el usuario final verá en la interfaz gráfica.
        """)

    with st.expander("¿Cómo importar el resultado en herramientas de traducción (CAT/TMS)?"):
        st.write("""
        Exporta el catálogo en formato **CSV**. La estructura generada es compatible con plataformas como Lokalise, Crowdin o Phrase, mapeando `Literal (ES)` como clave/fuente y las columnas `EN`, `CA`, `GL`, `EU` como valores destino.
        """)

    with st.expander("¿Qué hacer si el CSV da error al cargar?"):
        st.write("""
        LimpiaText detecta automáticamente delimitadores habituales (`;`, `,`, tabulador). Si persiste el fallo, comprueba que el archivo esté guardado con codificación **UTF-8** para evitar problemas con caracteres especiales.
        """)
