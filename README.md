# LimpiaText — Limpia archivos de HdUs de DevOps, detecta literales y los traduce.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://limpiatext.streamlit.app)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square)](https://www.python.org/)
[![Google GenAI SDK](https://img.shields.io/badge/Google%20GenAI-3.6%20Flash-FACC15?style=flat-square&labelColor=111111)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-black?style=flat-square)](License_LimpiaText.txt)

**LimpiaText** es una herramienta especializada en ingeniería de requisitos y localización de software multilingüe. Automatiza la extracción de literales de interfaz de usuario (UI) a partir de exportaciones de **Azure DevOps**, depura el marcado HTML residual de las Historias de Usuario (HDUs) y genera catálogos inmediatos de localización en lenguas autonómicas e inglés, incorporando métricas de fiabilidad y calidad funcional asistida por IA.

---

## 🎯 Problema que resuelve

En equipos ágiles de desarrollo de software, la extracción de textos de interfaz para traducción y parametrización suele ser un proceso manual propenso a errores:
1. **Ruido HTML y marcado enriquecido:** Las exportaciones de Azure DevOps contienen etiquetas HTML (`<div>`, `<p>`, `<span>`, `<!-- comments -->`) incrustadas en las descripciones y criterios de aceptación.
2. **Mezcla de prosa técnica y texto visible:** Diferenciar qué textos corresponden a botones/mensajes y cuáles son meras explicaciones funcionales consume tiempo de analistas y desarrolladores.
3. **Desfase en la localización multilingüe:** La traducción a idiomas oficiales y de soporte suele demorarse, bloqueando el desarrollo de vistas y archivos de recursos (`.json`, `.resx`, `.properties`).

---

## ✨ Características Principales

* 🧹 **Depuración HTML y normalización de texto:** Algoritmo de limpieza basado en expresiones regulares y decodificación de entidades HTML para extraer texto plano sin artefactos.
* 🤖 **Extracción inteligente de UI (Google Gemini 3.6 Flash):** Aislamiento estricto de elementos visuales (botones, etiquetas de campo, modales, opciones de desplegables, alertas y mensajes de validación), descartando la narrativa técnica.
* 🎯 **Métricas de Confianza IA & Sistema de Semáforo:**
  * **🟢 Alta (≥ 85%):** Textos explícitamente identificados como literales visuales en pantalla.
  * **🟡 Media (65% – 84%):** Textos inferidos a partir del contexto funcional o criterios de aceptación.
  * **🔴 Revisar (< 65%):** Textos ambiguos o con posible naturaleza técnica interna que requieren validación funcional previa.
* 🌐 **Localización Multilingüe Automática:**
  * **ES:** Español (Original)
  * **EN:** Inglés (Localización internacional)
  * **CA:** Catalán / Valenciano / Balear
  * **GL:** Gallego
  * **EU:** Euskera
* 📦 **Modo Demo Integrado:** Dataset de prueba representativo con historias de Azure DevOps para evaluar la herramienta con un solo clic sin necesidad de cargar archivos.
* 🛡️ **Procesamiento de JSON Robusto:** Mecanismo de parsing resiliente capaz de neutralizar bloques de marcado markdown o texto introductorio devuelto por el LLM.
* 📊 **Exportación Profesional:** Descarga directa en formatos **Excel (.xlsx)** estructurado y **CSV (separador `;` con codificación UTF-8-sig)**.
* 🎨 **Diseño Editorial Minimalista:** Interfaz responsiva inspirada en tipografía suiza y diseño editorial funcional.

---

## 🛠️ Arquitectura y Tecnologías

* **Frontend & UI:** [Streamlit](https://streamlit.io/) con inyección de CSS personalizado y Google Fonts (*Space Grotesk*, *Inter*).
* **Tratamiento y Análisis de Datos:** [Pandas](https://pandas.pydata.org/), `openpyxl`, `re`, `html`, `io`.
* **Motor de IA / NLP:** [Google GenAI SDK](https://pypi.org/project/google-genai/) ejecutando el modelo `gemini-3.6-flash` con *Structured Outputs* y *System Instructions* especializadas.

---

## 🚀 Instalación y Despliegue Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/BlueLaserGo/limpiatext.git
cd limpiatext
