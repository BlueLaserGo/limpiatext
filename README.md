# 🧹 LimpiaText: De DevOps al catálogo multilingüe sin dramas ✨

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://limpiatext.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/LLM-Gemini%203.6%20Flash-orange.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Automatización integral de extracción, clasificación y traducción de literales de interfaz de usuario (UI) procedentes de exportaciones de Azure DevOps.**

---

## 🎯 El problema real

En los equipos de análisis funcional y localización de software, la gestión de nuevos literales de interfaz presenta dos cuellos de botella clásicos:

1. **Exportaciones ruidosas:** Azure DevOps exporta las descripciones y criterios de aceptación con marcado HTML (`<div>`, `<span>`, `&nbsp;`), saltos de línea caóticos y comentarios de sistema.
2. **Extracción y traducción manual:** Localizar a mano cada botón, modal o campo nuevo para traducirlo a múltiples lenguas es un proceso lento, tedioso y propenso a inconsistencias.

---

## 🚀 La solución: LimpiaText

**LimpiaText** transforma este proceso manual en un flujo automatizado de 3 pasos:

1. **Limpieza con Regex y Pandas:** Elimina todo el ruido HTML y normaliza los textos de las Historias de Usuario (HDUs).
2. **Extracción y traducción con Gemini 3.6 Flash:** Aplica un prompt especializado con *Structured Outputs* (JSON estricto) que detecta únicamente elementos de interfaz (botones, selectores, errores, modales) y los clasifica por módulo y pantalla.
3. **Localización multilingüe:** Traduce los literales al **inglés** y a las **lenguas cooficiales españolas (catalán/valenciano/balear, gallego y euskera)** manteniendo el contexto funcional.
4. **Exportación inmediata a Excel (.xlsx):** Genera el catálogo estructurado listo para desarrollo, QA y traducción.

---

## 🛠️ Stack tecnológico

* **Frontend interactivo:** [Streamlit Community Cloud](https://streamlit.io/)
* **Orquestación LLM:** `google-genai` (Google Gemini 3.6 Flash)
* **Procesamiento de datos:** `pandas`, `re` (Regex), `html`
* **Generación de hojas de cálculo:** `openpyxl`

---

## 📋 Idiomas soportados

| Código | Idioma |
| :--- | :--- |
| **ES** | Español ES (Original) |
| **EN** | Inglés |
| **CA** | Catalán / Valenciano / Balear |
| **GL** | Gallego |
| **EU** | Euskera |

---

## 💻 Instalación y ejecución local

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/BlueLaserGo/limpiatext.git](https://github.com/BlueLaserGo/limpiatext.git)
   cd limpiatext
