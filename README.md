# 🧹 LimpiaText — Preparación y traducción de textos de UI

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.10+-111111?style=flat-square&logo=python&logoColor=FFDE00" alt="Python" />
  <img src="https://img.shields.io/badge/Streamlit-App-111111?style=flat-square&logo=streamlit&logoColor=FFDE00" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Google_GenAI-Gemini_3.6_Flash-111111?style=flat-square&logo=google&logoColor=FFDE00" alt="Gemini" />
  <img src="https://img.shields.io/badge/Human_in_the_loop-Supervised-111111?style=flat-square&logoColor=FFDE00" alt="Human in the loop" />
  <img src="https://img.shields.io/badge/Status-Portfolio_Project-FFDE00?style=flat-square&color=FFDE00&labelColor=111111" alt="Status" />
</p>

> 🎓 **Proyecto de portfolio · Ejercicio práctico**  
> 📄 **Documentación oficial:** Consulta y descarga la ficha técnica completa en [Ficha_Proyecto_LimpiaText_LauraSerrano.pdf](./Ficha_Proyecto_LimpiaText_LauraSerrano.pdf)

**LimpiaText** es una aplicación web interactiva diseñada para resolver un problema frecuente en equipos de producto, desarrollo y localización: **extraer, limpiar y preparar los textos visibles de una aplicación (botones, campos, mensajes y modales) a partir de historias de usuario en Azure DevOps**, para después generar sus versiones en múltiples idiomas.

---

## 🎯 ¿Por qué este proyecto?

Al redactar o exportar Historias de Usuario (HDUs) desde herramientas como Azure DevOps, la información suele llegar mezclada:

* 🧩 **Ruido técnico:** Marcado HTML residual (`<div>`, `<ul>`, `<b>`, etc.).
* 💬 **Contexto vs. Pantalla:** Explicaciones funcionales largas mezcladas con el texto que realmente verá el usuario final.
* 🌐 **Fricción lingüística:** Dificultad para aislar rápidamente los textos de interfaz para desarrolladores o herramientas de traducción (CAT/TMS).

Este proyecto explora cómo combinar **procesamiento de texto determinista (Regex)** con **modelos de lenguaje (IA)** y un flujo de **control humano (*Human-in-the-loop*)** para automatizar esta preparación sin perder precisión ni contexto.

---

## ⚙️ Arquitectura: Reglas → IA → Revisión humana

El flujo se apoya en tres capas bien diferenciadas:

* 📐 **1. Reglas y patrones (Python + Regex):**  
  Limpian de forma controlada y determinista las etiquetas HTML, listas y entidades codificadas en las descripciones y criterios de aceptación.
* 🤖 **2. Comprensión contextual (Gemini 3.6 Flash):**  
  Analiza la narrativa funcional, distingue qué partes son explicaciones internas y qué partes son componentes reales de pantalla (botones, etiquetas, modales, alertas) y los estructura en una tabla clara.
* 👩‍💻 **3. Control y supervisión humana (*Human-in-the-loop*):**  
  El usuario valida y edita directamente los textos extraídos en la interfaz antes de lanzar la traducción multilingüe a **Inglés (EN)**, **Catalán / Valenciano (CA)**, **Gallego (GL)** y **Euskera (EU)**.

---

## 🚀 Flujo de uso en 3 pasos

* 📁 **01 · Añade tus datos:**  
  Prueba de inmediato con el botón de datos de ejemplo o sube tu propio archivo CSV exportado de Azure DevOps.
* ✏️ **02 · Revisa y traduce:**  
  La IA propone la extracción de textos visibles. Puedes corregir cualquier celda en directo en la tabla editable y generar las versiones en los cuatro idiomas con un solo clic.
* 💾 **03 · Exporta:**  
  Descarga el catálogo estructurado en formato **Excel (.xlsx)** o **CSV (.csv)** con codificación UTF-8, listo para integrar en el código fuente o importar en plataformas como Lokalise, Phrase o Crowdin.

---

## 🛠️ Tecnologías utilizadas

| Área | Herramientas y Librerías |
| :--- | :--- |
| 🐍 **Núcleo & Lógica** | `Python 3.10+` · `Pandas` · `re (Regex)` |
| 🧠 **Inteligencia Artificial** | `Google GenAI SDK` (`gemini-3.6-flash`) |
| 🖥️ **Interfaz & UX** | `Streamlit` · `CSS3 personalizado` · `HTML5` |
| 📦 **Gestión de Archivos** | `OpenPyXL` · `BytesIO / StringIO` · `CSV (UTF-8-SIG)` |

---

## 💻 Instalación y ejecución local

Si deseas clonar y ejecutar este proyecto en tu entorno local:

1. 📥 **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/BlueLaserGo/limpiatext.git](https://github.com/BlueLaserGo/limpiatext.git)
   cd limpiatext
