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
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        max-width: 1100px;
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
        font-size: 1rem;
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

    /* Pestañas con acento amarillo */
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

    /* CONTROL ESTRICTO DE TAMAÑO EN BOTONES */
    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] {
        background-color: #111111 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: none !important;
        border: 1px solid #111111 !important;
        padding: 4px 12px !important;
        height: 32px !important;
        min-height: 32px !important;
        max-height: 32px !important;
        line-height: 1 !important;
        transition: all 0.15s ease !important;
    }

    div[data-testid="stButton"] button p,
    div[data-testid="stDownloadButton"] button p,
    button[data-testid="baseButton-secondary"] p,
    button[data-testid="baseButton-primary"] p {
        font-size: 0.78rem !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stButton"] button:hover,
    div[data-testid="stDownloadButton"] button:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background-color: #FACC15 !important;
        border-color: #FACC15 !important;
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
    
    # 3 botones compactos agrupados a la izquierda
    col_demo1, col_demo2, col_reset, _ = st.columns([1.6, 1.4, 1.1, 2.5])
    with col_demo1:
        if st.button("📁 Probar demo", use_container_width=True):
            st.session_state.df_devops = pd.read_csv(io.StringIO(EJEMPLO_CSV), sep=";")
            st.session_state.df_literales = None
            st.session_state.traducido = False
            st.rerun()

    with col_demo2:
        st.download_button(
            label="⬇ Muestra CSV",
            data=EJEMPLO_CSV.encode("utf-8-sig"),
            file_name="Export_DevOps_Sprint42_Sample.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_reset:
        if st.button("🔄 Limpiar", use_container_width=True):
            st.session_state.df_devops = None
            st.session_state.df_literales = None
            st.session_state.traducido = False
            st.rerun()

    archivo_subido = st.file_uploader(
        "O sube tu propio archivo CSV exportado de Azure DevOps:",
        type=["csv"]
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
        st.success(f"Datos cargados: **{len(df_act)}** Historias de Usuario listas.")
        
        with st.expander("Ver contenido original"):
            st.dataframe(df_act.head(3), use_container_width=True)
            
        col_btn1, _ = st.columns([2.0, 3.0])
        with col_btn1:
            btn_extraer = st.button("▶ Identificar textos de pantalla", use_container_width=True)
            
        if btn_extraer:
            if not api_key:
                st.error("Introduce tu Gemini API Key en la barra lateral para continuar.")
            else:
                with st.status("Procesando historias de usuario...", expanded=True) as estado:
                    st.write("🧹 Limpiando código HTML residual con reglas de expresiones regulares...")
                    
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

                    st.write("🤖 Identificando botones, campos y mensajes con Gemini...")
                    
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
                            'modulo': 'Módulo / Área',
                            'pantalla': 'Pantalla / Vista',
                            'tipo_elemento': 'Tipo de Elemento',
                            'texto_es': 'Texto en pantalla (ES)'
                        }
                        st.session_state.df_literales = df_res.rename(columns=columnas_renombradas)
                        st.session_state.traducido = False
                        estado.update(label="¡Textos identificados correctamente!", state="complete", expanded=False)
                    except Exception:
                        estado.update(label="Error en la extracción", state="error", expanded=False)
                        st.error("No se pudo estructurar el resultado.")
                        st.code(response.text)

    # Si ya se encontraron textos
    if st.session_state.df_literales is not None:
        st.write("---")
        st.markdown('<div class="step-header"><span class="step-badge">02</span> Revisa los textos encontrados</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="human-loop-banner">
            <b>La IA propone. Tú decides.</b> Revisa o corrige cualquier texto directamente en la tabla antes de generar las versiones en otros idiomas.
        </div>
        """, unsafe_allow_html=True)
        
        df_editado = st.data_editor(
            st.session_state.df_literales,
            use_container_width=True,
            num_rows="dynamic"
        )
        st.session_state.df_literales = df_editado

        if not st.session_state.traducido:
            st.write("")
            col_btn2, _ = st.columns([2.0, 3.0])
            with col_btn2:
                btn_traducir = st.button("🌐 Generar versiones (EN, CA, GL, EU)", use_container_width=True)
                
            if btn_traducir:
                if not api_key:
                    st.error("Introduce tu Gemini API Key en la barra lateral para continuar.")
                else:
                    with st.status("Traduciendo textos...", expanded=True) as estado_trad:
                        st.write("🌍 Adaptando términos a las cuatro lenguas...")
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
                                'modulo': 'Módulo / Área',
                                'pantalla': 'Pantalla / Vista',
                                'tipo_elemento': 'Tipo de Elemento',
                                'texto_es': 'Texto en pantalla (ES)',
                                'traduccion_en': 'Inglés (EN)',
                                'traduccion_ca': 'Catalán / Valenciano (CA)',
                                'traduccion_gl': 'Gallego (GL)',
                                'traduccion_eu': 'Euskera (EU)'
                            }
                            st.session_state.df_literales = df_trad.rename(columns=columnas_renombradas)
                            st.session_state.traducido = True
                            estado_trad.update(label="¡Traducciones completadas!", state="complete", expanded=False)
                            st.rerun()
                        except Exception:
                            estado_trad.update(label="Error en la traducción", state="error", expanded=False)
                            st.error("Error al procesar las traducciones.")
                            st.code(response.text)

        # BLOQUE DE DESCARGA
        st.write("---")
        st.markdown('<div class="step-header"><span class="step-badge">03</span> Exporta tus resultados</div>', unsafe_allow_html=True)
        
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
                    df_editado.to_excel(writer, index=False, sheet_name='Textos UI')
                data_file = output_excel.getvalue()
                nombre_archivo = "Textos_Interfaz_LimpiaText.xlsx"
                tipo_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                data_file = df_editado.to_csv(index=False, sep=";").encode("utf-8-sig")
                nombre_archivo = "Textos_Interfaz_LimpiaText.csv"
                tipo_mime = "text/csv"

            st.download_button(
                label=f"⬇ Descargar ({formato_descarga})",
                data=data_file,
                file_name=nombre_archivo,
                mime=tipo_mime
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
