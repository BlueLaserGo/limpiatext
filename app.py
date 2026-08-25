import streamlit as st
import pandas as pd
import json
import io
from google import genai
from google.genai import types

# Importamos la lógica desde utils.py
from utils import SYSTEM_PROMPT, limpiar_html_devops, obtener_columna

# 1. Configuración de página
st.set_page_config(
    page_title="LimpiaText — UI Localization",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilo Editorial Minimalista
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

    /* Botón examinar archivos */
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

    /* Ocultar texto nativo y poner en español */
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

# 3. Barra lateral
with st.sidebar:
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

    st.markdown("""
    <div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #D5D5D0; display: flex; align-items: center; gap: 8px;">
        <img src="https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg" 
             style="width: 28px; height: 28px; border-radius: 50%; object-fit: cover; border: 1px solid #CCCCCC; flex-shrink: 0;">
        <div style="line-height: 1.15;">
            <div style="font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.5px; color: #666666; font-weight: 600;">Desarrollado por</div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #222222;">Laura Serrano Gómez</div>
            <a href="https://www.linkedin.com/in/lauraserranogomez/" target="_blank" 
               style="font-size: 0.70rem; color: #666666; text-decoration: none;">LinkedIn ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 4. Encabezado principal
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

# Inicializar sesión para la tabla editada
if "df_literales" not in st.session_state:
    st.session_state.df_literales = None

# 5. Pestañas
tab_app, tab_guia = st.tabs(["🚀 Procesar Literales", "📖 Guía de Usuario & FAQ"])

with tab_app:
    archivo_subido = st.file_uploader(
        "Carga el CSV exportado de Azure DevOps (separador ';')",
        type=["csv"]
    )

    if archivo_subido:
        try:
            df_devops = pd.read_csv(archivo_subido, sep=";")
            st.success(f"Archivo cargado con éxito: **{len(df_devops)}** Historias de Usuario detectadas.")
            
            with st.expander("Vista previa del CSV original"):
                st.dataframe(df_devops.head(3), use_container_width=True)
                
            if st.button("Limpiar y Traducir Literales"):
                if not api_key:
                    st.error("Introduce tu Gemini API Key en la barra lateral para continuar.")
                else:
                    with st.spinner("Limpiando HTML y normalizando campos..."):
                        col_id = obtener_columna(df_devops, ["ID", "Id", "Work Item Id", "Id de elemento de trabajo"], 0)
                        col_title = obtener_columna(df_devops, ["Title", "Título"], 1)
                        col_desc = obtener_columna(df_devops, ["Description", "Descripción"], 2)
                        col_ac = obtener_columna(df_devops, ["Acceptance Criteria", "Criterios de Aceptación", "Criterios de aceptacion"], 3)
                        
                        df_devops["Description_Clean"] = df_devops[col_desc].apply(limpiar_html_devops) if col_desc else ""
                        df_devops["Acceptance_Criteria_Clean"] = df_devops[col_ac].apply(limpiar_html_devops) if col_ac else ""
                        
                        df_devops["Full_HDU_Text"] = (
                            "HDU ID: " + df_devops[col_id].astype(str) + "\n" +
                            "Título: " + df_devops[col_title].astype(str) + "\n" +
                            "Descripción: " + df_devops["Description_Clean"] + "\n" +
                            "Criterios de Aceptación: " + df_devops["Acceptance_Criteria_Clean"]
                        )
                        texto_completo_hdus = "\n\n---\n\n".join(df_devops["Full_HDU_Text"].tolist())

                    with st.spinner("Extrayendo literales con Gemini y generando traducciones..."):
                        client = genai.Client(api_key=api_key)
                        prompt_usuario = (
                            "A continuación tienes el conjunto de Historias de Usuario para procesar:\n\n"
                            f"{texto_completo_hdus}\n\n"
                            "Extrae todos los literales de UI, clasifícalos y tradúcelos según las directrices establecidas."
                        )
                        
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=prompt_usuario,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_PROMPT,
                                response_mime_type="application/json",
                                temperature=0.1
                            )
                        )
                        
                        try:
                            resultado_json = json.loads(response.text)
                        except Exception:
                            st.error("Gemini no devolvió un formato JSON válido.")
                            st.code(response.text)
                            st.stop()

                    with st.spinner("Estructurando catálogo final..."):
                        df_resultado = pd.DataFrame(resultado_json)
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
                        st.session_state.df_literales = df_resultado.rename(columns=columnas_renombradas)

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el archivo: {e}")

    # Mostrar la tabla editable y el bloque de exportación
    if st.session_state.df_literales is not None:
        st.write("---")
        st.subheader("Catálogo de UI Generado (Editable)")
        st.caption("Puedes hacer doble clic en cualquier celda para corregir o ajustar textos antes de descargar.")
        
        # Editor interactivo
        df_editado = st.data_editor(
            st.session_state.df_literales,
            use_container_width=True,
            num_rows="dynamic"
        )
        
        st.write("")
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
    st.markdown("### 📘 Manual de Uso")
    st.markdown("""
    1. **Exportar desde Azure DevOps:** Desde la consulta o backlog de tu iteración, exporta a CSV asegurando las columnas `ID`, `Title`, `Description` y `Acceptance Criteria` (separador `;`).
    2. **Cargar el archivo:** Sube el CSV en la pestaña principal.
    3. **Procesar:** Pulsa **Limpiar y Traducir Literales** para depurar el HTML y extraer los textos de UI.
    4. **Editar en vivo:** Revisa la tabla directamente en pantalla y modifica cualquier texto haciendo doble clic en la celda.
    5. **Descargar:** Selecciona formato Excel o CSV y descarga tu catálogo listo.
    """)
    st.markdown("---")
    st.markdown("### ❓ Preguntas Frecuentes (FAQ)")
    st.markdown("""
    * **¿Qué elementos de UI se extraen?**  
      Botones, nombres de campo, selectores, opciones de menú, modales, alertas y mensajes de error.
    * **¿Se ignoran requisitos técnicos?**  
      Sí, el modelo omite la narrativa técnica interna y extrae únicamente literales destinados a la interfaz de usuario.
    * **¿Qué idiomas cubre?**  
      Español original $\\rightarrow$ Inglés (EN), Catalán/Valenciano/Balear (CA), Gallego (GL) y Euskera (EU).
    """)
