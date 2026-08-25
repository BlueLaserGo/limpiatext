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
    layout="wide"
)

# 2. Estilo Editorial Minimalista (CSS personalizado)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

    /* Fondo general estilo papel y tipografía base */
    .stApp {
        background-color: #EFEFEF;
        color: #111111;
        font-family: 'Inter', sans-serif;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #E8E8E6;
        border-right: 1px solid #D5D5D0;
    }

    /* Encabezado brutalista / editorial */
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: -1.5px;
        text-transform: uppercase;
        line-height: 1;
        color: #111111;
        margin-bottom: 0.4rem;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #555555;
        line-height: 1.5;
        max-width: 800px;
        margin-bottom: 1.5rem;
    }

    /* Badge minimalista de versión */
    .version-tag {
        display: inline-block;
        background-color: #FACC15; /* Amarillo de acento */
        color: #111111;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.8rem;
    }

    /* Píldoras de idiomas en barra lateral */
    .lang-item {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        font-size: 0.88rem;
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

    /* Inputs y File Uploader con bordes nítidos */
    .stTextInput input {
        background-color: #FFFFFF !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 4px !important;
        color: #111111 !important;
    }
    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 1px dashed #AAAAAA;
        border-radius: 6px;
        padding: 1.2rem;
    }

    /* Botón de acción principal: Sólido con hover amarillo */
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
        border: none;
    }
    
    /* Botón de descarga */
    .stDownloadButton > button {
        background-color: #FACC15;
        color: #111111;
        border-radius: 4px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        border: 1px solid #111111;
        padding: 0.6rem 2rem;
    }
    .stDownloadButton > button:hover {
        background-color: #111111;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# 3. Funciones de limpieza y soporte
def limpiar_html_devops(texto: str) -> str:
    """Limpia etiquetas HTML, comentarios y entidades de DevOps."""
    if not isinstance(texto, str) or not texto.strip():
        return ""
    texto = html.unescape(texto)
    texto = re.sub(r'<!--.*?-->', '', texto, flags=re.DOTALL)
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

SYSTEM_PROMPT = """
Eres una analista funcional senior y especialista en localización de software multilingüe para el ámbito autonómico e internacional.
Tu tarea es analizar las Historias de Usuario (HDUs) de una iteración, una vez ya han sido refinadas, de una aplicación de software de gestión y extraer ÚNICAMENTE los literales que sean nuevos de interfaz (UI):
- Nombres de campos, botones, pestañas, títulos de nuevos formularios y ventanas, y selectores.
- Mensajes de validación, alertas, mensajes de error, modales o toasts.
- Opciones de menús desplegables y títulos de sección.

NO extraigas descripciones narrativas ni requisitos técnicos. Extrae solo textos visibles para el usuario final en la UI.

Para cada literal encontrado, debes proporcionar:
1. id_hdu: El ID de la Historia de Usuario correspondiente.
2. modulo: El área funcional o módulo (ej. Finanzas, Obras, Contabilidad).
3. pantalla: La vista o contexto dentro del módulo.
4. tipo_elemento: Tipo de elemento (Botón, Campo, Mensaje de error, Alerta, Opción desplegable, etc.).
5. texto_es: El literal original en español.
6. traduccion_en: Traducción profesional al inglés.
7. traduccion_ca: Traducción profesional al catalán / valenciano / balear.
8. traduccion_gl: Traducción profesional al gallego.
9. traduccion_eu: Traducción profesional al euskera.

IMPORTANTE: Debes responder EXCLUSIVAMENTE con una lista JSON válida de objetos.
"""

# 4. Barra lateral
with st.sidebar:
    st.markdown('<div class="hero-title" style="font-size: 1.6rem;">LimpiaText</div>', unsafe_allow_html=True)
    st.caption("De DevOps al catálogo multilingüe sin dramas.")
    st.write("---")
    
    api_key_env = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input(
        "Gemini API Key:",
        value=api_key_env,
        type="password",
        help="Clave de Google AI Studio (modelo: gemini-3.6-flash)."
    )
    
    st.markdown("---")
    st.markdown("**Idiomas de exportación:**")
    st.markdown("""
    <div style="margin-top: 10px;">
        <div class="lang-item"><span class="lang-badge">EN</span> Inglés</div>
        <div class="lang-item"><span class="lang-badge">CA</span> Catalán / Valenciano</div>
        <div class="lang-item"><span class="lang-badge">GL</span> Gallego</div>
        <div class="lang-item"><span class="lang-badge">EU</span> Euskera</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-top: 10px;">
        <img src="https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg" 
             style="width: 48px; height: 48px; min-width: 48px; border-radius: 50%; object-fit: cover; border: 1px solid #111111;">
        <div style="line-height: 1.25;">
            <div style="font-weight: 700; color: #111111; font-size: 0.9rem;">Laura Serrano Gómez</div>
            <a href="https://www.linkedin.com/in/lauserrano/?locale=es-ES" target="_blank" style="color: #555555; text-decoration: underline; font-size: 0.8rem;">Conectar en LinkedIn ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 5. Encabezado principal (Hero Editorial)
st.markdown('<span class="version-tag">DevOps → Catalog Pipeline</span>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">LimpiaText</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">'
    'Extracción inteligente de literales de interfaz desde exportaciones de <b>Azure DevOps</b>, '
    'depuración de marcado HTML residual y catálogo de localización multilingüe inmediato.'
    '</div>',
    unsafe_allow_html=True
)

st.write("---")

# 6. Pestañas de contenido
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
                st.dataframe(df_devops.head(3))
                
            if st.button("Limpiar y Traducir Literales"):
                if not api_key:
                    st.error("Introduce tu Gemini API Key en la barra lateral para continuar.")
                else:
                    with st.spinner("Limpiando HTML y normalizando campos..."):
                        col_desc = "Description" if "Description" in df_devops.columns else df_devops.columns[1]
                        col_ac = "Acceptance Criteria" if "Acceptance Criteria" in df_devops.columns else df_devops.columns[2]
                        
                        df_devops["Description_Clean"] = df_devops[col_desc].apply(limpiar_html_devops)
                        df_devops["Acceptance_Criteria_Clean"] = df_devops[col_ac].apply(limpiar_html_devops)
                        
                        df_devops["Full_HDU_Text"] = (
                            "HDU ID: " + df_devops["ID"].astype(str) + "\n" +
                            "Título: " + df_devops["Title"].astype(str) + "\n" +
                            "Descripción: " + df_devops["Description_Clean"] + "\n" +
                            "Criterios de Aceptación: " + df_devops["Acceptance_Criteria_Clean"]
                        )
                        texto_completo_hdus = "\n\n---\n\n".join(df_devops["Full_HDU_Text"].tolist())

                    with st.spinner("Extrayendo literales con Gemini 3.6 Flash y generando traducciones..."):
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
                        resultado_json = json.loads(response.text)

                    with st.spinner("Estructurando catálogo final..."):
                        df_literales = pd.DataFrame(resultado_json)
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
                        df_literales = df_literales.rename(columns=columnas_renombradas)
                        
                        output_excel = io.BytesIO()
                        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                            df_literales.to_excel(writer, index=False, sheet_name='Catálogo UI')
                        excel_data = output_excel.getvalue()

                    st.write("---")
                    st.subheader("Catálogo de UI Generado")
                    st.dataframe(df_literales, use_container_width=True)
                    
                    st.download_button(
                        label="Descargar Catálogo Excel (.xlsx)",
                        data=excel_data,
                        file_name="Catalogo_Literales_LimpiaText.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el archivo: {e}")

with tab_guia:
    st.markdown("### 📘 Manual de Uso")
    st.markdown("""
    1. **Exportar desde Azure DevOps:** Desde la consulta o backlog de tu iteración, exporta a CSV con las columnas `ID`, `Title`, `Description` y `Acceptance Criteria` (separador `;`).
    2. **Cargar el archivo:** Sube el CSV en la pestaña principal.
    3. **Procesar:** Pulsa el botón de extracción para depurar etiquetas HTML y generar el catálogo multilingüe.
    4. **Descargar:** Obtén el archivo `.xlsx` listo para desarrollo y traductores.
    """)
    st.markdown("---")
    st.markdown("### ❓ Preguntas Frecuentes (FAQ)")
    st.markdown("""
    * **¿Por qué se ignoran explicaciones largas?**  
      LimpiaText detecta únicamente texto visible para el usuario final en la UI (botones, selectores, campos, errores, alertas) y descarta la narrativa técnica.
    * **¿Qué idiomas se traducen?**  
      Español original $\\rightarrow$ Inglés (EN), Catalán/Valenciano/Balear (CA), Gallego (GL) y Euskera (EU).
    """)
