import html
import re

SYSTEM_PROMPT = """
Eres una analista funcional senior y especialista en localización de software multilingüe para el ámbito autonómico e internacional.
Tu tarea es analizar las Historias de Usuario (HDUs) de una iteración, una vez ya han sido refinadas, de una aplicación de software de gestión y extraer ÚNICAMENTE los literales que sean nuevos de interfaz (UI):
- Nombres de campos, botones, pestañas, títulos de nuevos formularios y ventanas, y selectores.
- Mensajes de validación, alertas, mensajes de error, modales o toasts.
- Opciones de menús desplegables y títulos de sección.

NO extraigas descripciones narrativas ni requisitos técnicos. Extrae solo textos visibles para el usuario final en la UI.

Estructura obligatoria de respuesta JSON:
[
  {
    "id_hdu": "ID",
    "modulo": "Módulo Funcional",
    "pantalla": "Pantalla / Vista",
    "tipo_elemento": "Tipo de Elemento",
    "texto_es": "Literal (ES)",
    "traduccion_en": "Inglés (EN)",
    "traduccion_ca": "Catalán / Valenciano / Balear (CA)",
    "traduccion_gl": "Gallego (GL)",
    "traduccion_eu": "Euskera (EU)"
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
