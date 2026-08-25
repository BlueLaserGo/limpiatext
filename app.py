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
    page_title="LimpiaText - Extractor & Traductor de UI",
    page_icon="🧹",
    layout="wide"
)

# 2. Estilos visuales personalizados (CSS)
st.markdown("""
<style>
    /* Fondo principal y tipografía */
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
    }
    
    /* Barra lateral estilizada */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Cajas de entrada */
    .stTextInput input, .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
        background-color: #FFFFFF;
        color: #0F172A;
    }
    
    /* Botón principal */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.8rem;
        transition: all 0.2s ease;
    }
    
    /* Píldoras de idiomas */
    .lang-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        font-size: 0.9rem;
    }
    .lang-badge {
        background: #E2E8F0;
        color: #1E293B;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-family: monospace;
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

# 4. Barra lateral (Configuración)
with st.sidebar:
    st.title("🧹 LimpiaText")
    st.caption("De DevOps al catálogo multilingüe sin dramas.")
    
    api_key_env = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input(
        "Introduce tu Gemini API Key:",
        value=api_key_env,
        type="password",
        help="Clave de Google AI Studio (modelo configurado: gemini-3.6-flash). Si está en los Secrets de Streamlit, se detecta sola."
    )
    
    st.markdown("---")
    st.markdown("**Idiomas soportados:**")
    st.markdown("""
    <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 6px;">
        <div class="lang-item"><span class="lang-badge">EN</span> Inglés</div>
        <div class="lang-item"><span class="lang-badge">CA</span> Catalán / Valenciano / Balear</div>
        <div class="lang-item"><span class="lang-badge">GL</span> Gallego</div>
        <div class="lang-item"><span class="lang-badge">EU</span> Euskera</div>
    </div>
    """, unsafe_allow_html=True)

# 5. Encabezado principal
st.title("🧹 LimpiaText")
st.write(
    "Automatiza la extracción de literales de interfaz desde exportaciones de Azure DevOps, "
    "elimina el marcado HTML y genera el catálogo de traducción al **inglés y las lenguas cooficiales** en un clic."
)

# 6. Carga de archivo
archivo_subido = st.file_uploader(
    "Carga el CSV exportado de DevOps (separador ';')",
    type=["csv"]
)

if archivo_subido:
    try:
        df_devops = pd.read_csv(archivo_subido, sep=";")
        st.success(f"Archivo cargado con **{len(df_devops)}** Historias de Usuario detectadas.")
        
        with st.expander("👀 Vista previa del CSV original"):
            st.dataframe(df_devops.head(3))
            
        if st.button("🚀 Limpiar y Traducir con IA", type="primary"):
            if not api_key:
                st.error("⚠️ Falta la Gemini API Key. Introdúcela en la barra lateral.")
            else:
                with st.spinner("🧹 Limpiando HTML y formateando texto plano..."):
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

                with st.spinner("🤖 Extrayendo literales y traduciendo a EN, CA, GL y EU..."):
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

                with st.spinner("📊 Estructurando catálogo final..."):
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

                st.balloons()
                st.subheader("📋 Catálogo de UI Listo para Desarrollo")
                st.dataframe(df_literales, use_container_width=True)
                
                st.download_button(
                    label="📥 Descargar Catálogo Multilingüe en Excel (.xlsx)",
                    data=excel_data,
                    file_name="Catalogo_Literales_LimpiaText.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
