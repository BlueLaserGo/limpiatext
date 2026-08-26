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

# 2. Estilo Editorial Minimalista (CSS)
st.markdown("""
<style>
    @import url('[https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap](https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Inter:wght@400;500;600&display=swap)');

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
    """Limpia markdown residual o texto extra para evitar JSONDecodeError."""
    texto_limpio = texto_respuesta.strip()
    if texto_limpio.startswith("```"):
        texto_limpio = re.sub(r'^```[a-zA-Z]*\n?', '', texto_limpio)
        texto_limpio = re.sub(r'\n?```$', '', texto_limpio)
    
    # Busca la primera lista JSON válida en el texto
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

    st.write("---")
    
    # Autoría discreta y elegante en el pie del sidebar
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-top: 1.5rem;">
        <img src="https://raw.githubusercontent.com/BlueLaserGo/limpiatext/main/avatar_lasergo.jpeg" 
             style="width: 28px; height: 28px; border-radius: 50%; object-fit: cover; border: 1px solid #CCCCCC; flex-shrink: 0;">
        <div style="line-height: 1.15;">
            <div style="font-size: 0.76rem; font-weight: 600; color: #222222;">Laura Serrano Gómez</div>
            <a href="https://www.linkedin.com/in/lauraserranogomez/" target="_blank" style="font-size: 0.68rem; color: #666666; text-decoration: none;">LinkedIn ↗</a>
        </div>
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
                        client = genai.Client(api_key=api_key)
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
                        
                        # Cálculo de Estado a partir de Confianza IA
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
                        
                        # Reordenar columnas para visualización clara
                        orden_cols = [
                            'ID HDU', 'Módulo Funcional', 'Pantalla / Vista', 'Tipo de Elemento',
                            'Literal (ES)', 'Confianza IA', 'Estado',
                            'Inglés (EN)', 'Catalán / Valenciano (CA)', 'Gallego (GL)', 'Euskera (EU)'
                        ]
                        cols_existentes = [c for c in orden_cols if c in df_literales.columns]
                        df_literales = df_literales[cols_existentes]

                        # Preparar exportación Excel
                        output_excel = io.BytesIO()
                        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                            df_literales.to_excel(writer, index=False, sheet_name='Catálogo UI')
                        excel_data = output_excel.getvalue()

                        # Preparar exportación CSV
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

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el archivo: {e}")

with tab_guia:
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns(2, gap="medium")
    
    with col_g1:
        card_pasos = (
            '<div style="background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 8px; '
            'padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); min-height: 260px;">'
            '<div style="display: inline-block; background-color: #FACC15; color: #111111; font-family: \'Space Grotesk\', sans-serif; '
            'font-weight: 700; font-size: 0.72rem; padding: 3px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.8rem;">'
            'Flujo Funcional'
            '</div>'
            '<div style="font-family: \'Space Grotesk\', sans-serif; font-weight: 700; font-size: 1.1rem; color: #111111; margin-bottom: 0.8rem;">'
            '🚀 Proceso en 4 Pasos'
            '</div>'
            '<div style="font-size: 0.88rem; line-height: 1.6; color: #333333;">'
            '<b>1. Exportar:</b> Descarga el CSV desde Azure DevOps con separador punto y coma (<code>;</code>).<br>'
            '<b>2. Cargar:</b> Sube el archivo en el panel superior.<br>'
            '<b>3. Procesar:</b> Depuración de HTML y extracción de literales con IA.<br>'
            '<b>4. Descargar:</b> Obtén el catálogo final en <b>Excel (.xlsx)</b> o <b>CSV</b>.'
            '</div>'
            '</div>'
        )
        st.markdown(card_pasos, unsafe_allow_html=True)

    with col_g2:
        card_confianza = (
            '<div style="background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 8px; '
            'padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); min-height: 260px;">'
            '<div style="display: inline-block; background-color: #111111; color: #FFDE00; font-family: \'Space Grotesk\', monospace; '
            'font-weight: 700; font-size: 0.72rem; padding: 3px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.8rem;">'
            'Control de Calidad'
            '</div>'
            '<div style="font-family: \'Space Grotesk\', sans-serif; font-weight: 700; font-size: 1.1rem; color: #111111; margin-bottom: 0.8rem;">'
            '🎯 Métricas de Confianza IA'
            '</div>'
            '<div style="font-size: 0.86rem; line-height: 1.6; color: #333333;">'
            '<b>🟢 Alta (≥ 85%):</b> Botones, modales y etiquetas visibles confirmadas.<br>'
            '<b>🟡 Media (65% – 84%):</b> Literales inferidos del contexto funcional.<br>'
            '<b>🔴 Revisar (&lt; 65%):</b> Posibles reglas de negocio o textos técnicos a revisar.'
            '</div>'
            '</div>'
        )
        st.markdown(card_confianza, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
    
    card_faq = (
        '<div style="background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 8px; '
        'padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">'
        '<div style="font-family: \'Space Grotesk\', sans-serif; font-weight: 700; font-size: 1.1rem; color: #111111; margin-bottom: 0.8rem;">'
        '❓ Preguntas Frecuentes (FAQ)'
        '</div>'
        '<div style="font-size: 0.88rem; line-height: 1.6; color: #333333;">'
        '<b>¿Por qué se ignoran las descripciones largas?</b><br>'
        'LimpiaText actúa como filtro de calidad funcional: extrae exclusivamente los literales de pantalla (UI) y descarta la prosa técnica interna.<br><br>'
        '<b>¿Qué idiomas traduce?</b><br>'
        'Español (ES) original &rarr; <b>Inglés (EN)</b>, <b>Catalán / Valenciano / Balear (CA)</b>, <b>Gallego (GL)</b> y <b>Euskera (EU)</b>.'
        '</div>'
        '</div>'
    )
    st.markdown(card_faq, unsafe_allow_html=True)

    with col_g2:
        st.markdown("""
        <div style="background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 8px; padding: 1.4rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03); height: 100%;">
            <div style="font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05rem; text-transform: uppercase; letter-spacing: 0.5px; color: #111111; margin-bottom: 0.8rem; border-bottom: 2px solid #FACC15; padding-bottom: 4px; display: inline-block;">
                🎯 Criterios de Confianza IA
            </div>
            <div style="font-size: 0.86rem; line-height: 1.55; color: #333333;">
                <div style="margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #111111;">🟢 Alta (≥ 85%):</span> Literales explícitos de pantalla (botones, etiquetas de campo, títulos de modal, mensajes de error literales).
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #111111;">🟡 Media (65% – 84%):</span> Literales inferidos a partir del contexto funcional o criterios de aceptación.
                </div>
                <div>
                    <span style="font-weight: 700; color: #111111;">🔴 Revisar (&lt; 65%):</span> Textos ambiguos o con posible naturaleza técnica interna que requieren validación funcional previa.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #FFFFFF; border: 1px solid #D5D5D0; border-radius: 8px; padding: 1.4rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
        <div style="font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.05rem; text-transform: uppercase; letter-spacing: 0.5px; color: #111111; margin-bottom: 0.8rem; border-bottom: 2px solid #FACC15; padding-bottom: 4px; display: inline-block;">
            ❓ Preguntas Frecuentes (FAQ)
        </div>
        <div style="font-size: 0.88rem; line-height: 1.6; color: #333333;">
            <p style="margin-bottom: 8px;"><b>¿Por qué se descartan textos narrativos largos?</b><br>
            LimpiaText aplica un filtro funcional estricto: extrae exclusivamente los literales destinados a los archivos de recursos de interfaz (UI), eliminando descripciones técnicas y reglas de negocio internas.</p>
            <p style="margin-bottom: 0;"><b>¿Qué idiomas incluye el catálogo?</b><br>
            Español original $\\rightarrow$ <b>Inglés (EN)</b>, <b>Catalán / Valenciano / Balear (CA)</b>, <b>Gallego (GL)</b> y <b>Euskera (EU)</b>.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with col_g2:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #D5D5D0; border-radius:6px; padding:1.2rem; height:100%;">
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1rem; margin-bottom:0.6rem; color:#111111;">
                🎯 Niveles de Confianza IA
            </div>
            <div style="font-size:0.86rem; line-height:1.5; color:#333333;">
                <div style="margin-bottom:8px;">
                    <span style="font-weight:700;">🟢 Alta (≥ 85%):</span> Literales explícitos de pantalla (botones, etiquetas, títulos de modal, mensajes de error literales).
                </div>
                <div style="margin-bottom:8px;">
                    <span style="font-weight:700;">🟡 Media (65% - 84%):</span> Literales contextuales o deducidos de los criterios de aceptación.
                </div>
                <div>
                    <span style="font-weight:700;">🔴 Revisar (&lt; 65%):</span> Textos que podrían ser descripciones funcionales internas o reglas de negocio que requieren validación funcional.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #D5D5D0; border-radius:6px; padding:1.2rem;">
        <div style="font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1rem; margin-bottom:0.6rem; color:#111111;">
            ❓ Preguntas Frecuentes (FAQ)
        </div>
        <div style="font-size:0.88rem; line-height:1.6; color:#444444;">
            <p><b>¿Por qué se ignoran descripciones largas o narrativas?</b><br>
            LimpiaText actúa como filtro de calidad funcional: extrae exclusivamente los elementos que formarán parte de los archivos de localización de la aplicación (UI), descartando la prosa técnica interna.</p>
            <p style="margin-bottom:0;"><b>¿Qué idiomas cubre el catálogo automático?</b><br>
            Español original $\\rightarrow$ <b>Inglés (EN)</b>, <b>Catalán / Valenciano / Balear (CA)</b>, <b>Gallego (GL)</b> y <b>Euskera (EU)</b>.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
