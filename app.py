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

# 2. Estilo limpio y robusto
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;600&display=swap');

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    .stApp {
        background-color: #F8F9FA;
        color: #111111;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #EEEEEE;
        border-right: 1px solid #D5D5D0;
    }
    .hero-badge {
        display: inline-block;
        background-color: #FACC15;
        color: #111111;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -1px;
        text-transform: uppercase;
        color: #111111;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #555555;
        line-height: 1.4;
        max-width: 800px;
        margin-bottom: 1.5rem;
    }
    .lang-item {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        font-size: 0.85rem;
        color: #222222;
    }
    .lang-badge {
        background: #111111;
        color: #FFFFFF;
        font-family: 'Space Grotesk', monospace;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 2px;
        font-size: 0.75rem;
    }
    .stButton > button {
        background-color: #111111;
        color: #FFFFFF;
        border-radius: 4px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        border: none;
        padding: 0.6rem 2rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #FACC15;
        color: #111111;
    }
</style>
""", unsafe_allow_html=True)

# 3. Funciones de soporte
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

SYSTEM_PROMPT = """
Eres una analista funcional senior y especialista en localización de software multilingüe.
Tu tarea es analizar las Historias de Usuario (HDUs) de Azure DevOps y extraer ÚNICAMENTE los literales visibles de interfaz de usuario (UI):
- Nombres de campos, botones, pestañas, títulos de formularios, ventanas y selectores.
- Mensajes de validación, errores, modales y alertas.
- Opciones de listas desplegables.

Ignora descripciones narrativas y requisitos técnicos internos.

Devuelve EXCLUSIVAMENTE una lista JSON válida de objetos con esta estructura:
[
  {
    "id_hdu": "ID",
    "modulo": "Módulo funcional",
    "pantalla": "Pantalla o vista",
    "tipo_elemento": "Botón/Campo/Mensaje...",
    "texto_es": "Texto original en español",
    "traduccion_en": "Traducción inglés",
    "traduccion_ca": "Traducción catalán/valenciano/balear",
    "traduccion_gl": "Traducción gallego",
    "traduccion_eu": "Traducción euskera"
  }
]
"""

# 4. Barra lateral
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.8rem; padding-bottom: 0.6rem; border-bottom: 1px solid #D5D5D0;">
        <img src="https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg" 
             style="width: 38px; height: 38px; border-radius: 50%; object-fit: cover; border: 1px solid #CCCCCC; flex-shrink: 0;">
        <div style="line-height: 1.2;">
            <div style="font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.5px; color: #666666; font-weight: 600;">Desarrollado por</div>
            <div style="font-size: 0.88rem; font-weight: 700; color: #111111;">Laura Serrano Gómez</div>
            <a href="https://www.linkedin.com/in/lauraserranogomez/" target="_blank" style="font-size: 0.75rem; color: #0066CC; text-decoration: none; font-weight: 500;">Conectar en LinkedIn ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    api_key = st.text_input("Gemini API Key:", type="password", help="Introduce tu API Key de Google Gemini.")

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

# 5. Encabezado principal
st.markdown('<div class="hero-badge">Extracción y traducción de literales</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">LimpiaText</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">'
    'Extracción inteligente de literales de interfaz desde exportaciones de <b>Azure DevOps</b>, '
    'depuración de marcado HTML residual y catálogo de localización multilingüe inmediato.'
    '</div>',
    unsafe_allow_html=True
)

# 6. Pestañas de contenido
tab_app, tab_guia = st.tabs(["🚀 Procesar Literales", "📖 Guía de Usuario & FAQ"])

with tab_app:
    archivo_subido = st.file_uploader(
        "Carga el CSV exportado de Azure DevOps (separador ';')",
        type=["csv"],
        help="Máximo 200 MB por archivo en formato CSV."
    )

    if archivo_subido:
        try:
            df_devops = pd.read_csv(archivo_subido, sep=";")
            st.success(f"Archivo cargado: **{len(df_devops)}** elementos encontrados.")
            
            with st.expander("Vista previa de datos cargados"):
                st.dataframe(df_devops.head(3), use_container_width=True)
                
            if st.button("Limpiar y Traducir Literales"):
                if not api_key:
                    st.error("Introduce tu Gemini API Key en la barra lateral para continuar.")
                else:
                    with st.spinner("Procesando y limpiando texto..."):
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
                        texto_completo = "\n\n---\n\n".join(df_devops["Full_HDU_Text"].tolist())

                    with st.spinner("Extrayendo literales con Gemini y traduciendo..."):
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=f"Procesa las siguientes Historias de Usuario:\n\n{texto_completo}",
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_PROMPT,
                                response_mime_type="application/json",
                                temperature=0.1
                            )
                        )
                        
                        try:
                            resultado_json = json.loads(response.text)
                        except Exception:
                            st.error("Respuesta no válida del modelo. Inténtalo de nuevo.")
                            st.code(response.text)
                            st.stop()

                    with st.spinner("Generando catálogo..."):
                        df_literales = pd.DataFrame(resultado_json)
                        df_literales = df_literales.rename(columns={
                            'id_hdu': 'ID HDU',
                            'modulo': 'Módulo Funcional',
                            'pantalla': 'Pantalla / Vista',
                            'tipo_elemento': 'Tipo de Elemento',
                            'texto_es': 'Literal (ES)',
                            'traduccion_en': 'Inglés (EN)',
                            'traduccion_ca': 'Catalán / Valenciano (CA)',
                            'traduccion_gl': 'Gallego (GL)',
                            'traduccion_eu': 'Euskera (EU)'
                        })
                        
                        output_excel = io.BytesIO()
                        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                            df_literales.to_excel(writer, index=False, sheet_name='Catálogo UI')
                        excel_data = output_excel.getvalue()

                    st.write("---")
                    st.subheader("Catálogo de Literales Extraídos")
                    st.dataframe(df_literales, use_container_width=True)
                    
                    st.download_button(
                        label="Descargar Catálogo Excel (.xlsx)",
                        data=excel_data,
                        file_name="Catalogo_Literales_LimpiaText.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

with tab_guia:
    st.markdown("### 📘 Manual de Uso")
    st.markdown("""
    1. **Exportar desde Azure DevOps:** Descarga el CSV de tu backlog/iteración con las columnas habituales (separador `;`).
    2. **Cargar archivo:** Sube el archivo en la pestaña principal.
    3. **Procesar:** Pulsa el botón para extraer automáticamente los literales de UI y traducirlos.
    4. **Descargar:** Obtén el archivo `.xlsx` listo para desarrollo y localización.
    """)
    st.markdown("---")
    st.markdown("### ❓ Preguntas Frecuentes")
    st.markdown("""
    * **¿Qué elementos extrae?** Botones, nombres de campo, selectores, modales y mensajes de error o alerta.
    * **¿Qué idiomas cubre?** Español original, Inglés (EN), Catalán/Valenciano/Balear (CA), Gallego (GL) y Euskera (EU).
    """)
