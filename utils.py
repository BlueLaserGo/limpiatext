import html
import re

PROMPT_EXTRACCION = """
Eres una analista funcional senior de software.
Analiza las Historias de Usuario (HDUs) de Azure DevOps y extrae ÚNICAMENTE los literales nuevos de interfaz (UI):
- Nombres de campos, botones, pestañas, títulos de formularios/ventanas y selectores.
- Mensajes de validación, alertas, mensajes de error, modales o toasts.
- Opciones de menús desplegables y títulos de sección.

NO extraigas descripciones narrativas ni requisitos técnicos. Extrae solo textos visibles para el usuario final en la UI en su idioma original (español).

Estructura obligatoria de respuesta JSON:
[
  {
    "id_hdu": "ID",
    "modulo": "Módulo Funcional",
    "pantalla": "Pantalla / Vista",
    "tipo_elemento": "Tipo de Elemento",
    "texto_es": "Literal (ES)"
  }
]
"""

PROMPT_TRADUCCION = """
Eres una especialista en localización de software multilingüe para el ámbito autonómico e internacional.
Se te proporciona una lista JSON de literales de interfaz en español.
Para cada elemento, genera las traducciones profesionales a inglés, catalán/valenciano/balear, gallego y euskera manteniendo los datos previos.

Estructura obligatoria de respuesta JSON:
[
  {
    "id_hdu": "ID previo",
    "modulo": "Módulo previo",
    "pantalla": "Pantalla previa",
    "tipo_elemento": "Tipo previo",
    "texto_es": "Literal previo (ES)",
    "traduccion_en": "Traducción profesional al inglés",
    "traduccion_ca": "Traducción profesional al catalán / valenciano / balear",
    "traduccion_gl": "Traducción profesional al gallego",
    "traduccion_eu": "Traducción profesional al euskera"
  }
]
"""

def limpiar_html_devops(texto: str) -> str:
    """Limpia etiquetas HTML, comentarios y entidades de Azure DevOps."""
    if not isinstance(texto, str) or not texto.strip():
        return ""
    texto = html.unescape(texto)
    texto = re.sub(r'<!--.*?-->', '', texto, flags=re.DOTALL)
    texto = re.sub(r'<[^>]+>', '', texto)
    return re.sub(r'\s+', ' ', texto).strip()

def obtener_columna(df, opciones_nombres, indice_defecto=0):
    """Busca una columna por diferentes variantes de nombre."""
    for col in df.columns:
        if col.strip().lower() in [op.lower() for op in opciones_nombres]:
            return col
    return df.columns[indice_defecto] if len(df.columns) > indice_defecto else None
