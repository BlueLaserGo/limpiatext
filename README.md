# 🧹 LimpiaText — UI Localization Engine

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Google%20Gemini-3.6%20Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white" alt="Gemini 3.6 Flash" />
  <img src="https://img.shields.io/badge/Azure%20DevOps-Supported-0078D7?style=for-the-badge&logo=azuredevops&logoColor=white" alt="Azure DevOps" />
</p>

> Extracción funcional, depuración de marcado HTML y catálogo de localización multilingüe a partir de Historias de Usuario exportadas de **Azure DevOps**.
---

## 🎯 Problema y Contexto

En entornos ágiles gestionados con Azure DevOps, los requisitos de interfaz de usuario (UI) suelen redactarse dentro de campos enriquecidos de texto (`Description` y `Acceptance Criteria`). Esto introduce etiquetas HTML complejas (`<div>`, `<span>`, `<ul>`, comentarios y entidades codificadas) junto con descripciones funcionales y técnicas no aptas para el catálogo directo de cadenas.

**LimpiaText** cierra la brecha entre el análisis funcional, la ingeniería y los equipos de localización:

* Depura automáticamente el marcado HTML residual y normaliza el texto.
* Aísla de forma inteligente únicamente los literales visibles de cara al usuario final (botones, títulos, campos, modales, alertas, selectores).
* Ofrece un flujo secuencial en **2 pasos** con validación y edición humana antes del procesado lingüístico.
* Genera traducciones especializadas hacia lenguas cooficiales e inglés.

---

## 🏗️ Flujo de Operación

* **01. Entrada:** Subida del archivo CSV o carga de datos de prueba con un solo clic.
* **02. Depuración:** Filtro Regex y limpieza de entidades HTML residuales de Azure DevOps.
* **03. Extracción:** Identificación de literales de interfaz en español mediante Gemini 3.6 Flash.
* **04. Validación:** Edición y ajuste manual interactivo de las cadenas en vivo (`st.data_editor`).
* **05. Localización:** Traducción a inglés, catalán/valenciano/balear, gallego y euskera.
* **06. Exportación:** Generación del catálogo estructurado en formato Excel (`.xlsx`) o CSV (`.csv`).

---

## ⚙️ Arquitectura Funcional

| Fase | Componente | Descripción |
| --- | --- | --- |
| **01. Carga / Demo** | `st.file_uploader` | Detección automática de delimitadores (`;`, `,`, tabulador) o carga de muestra con un clic. |
| **02. Depuración** | `utils.py` (Regex) | Limpieza de entidades HTML, etiquetas residuales y comentarios de Azure DevOps. |
| **03. Extracción** | Gemini 3.6 Flash | Identificación y aislamiento de cadenas de interfaz en español. |
| **04. Edición** | `st.data_editor` | Interfaz interactiva de validación para modificar, agregar o depurar filas en vivo. |
| **05. Localización** | Gemini 3.6 Flash | Traducción simultánea a **Inglés (EN)**, **Catalán/Valenciano (CA)**, **Gallego (GL)** y **Euskera (EU)**. |
| **06. Exportación** | Pandas / OpenPyXL | Descarga en formato `.xlsx` con hojas nombradas o `.csv` con codificación UTF-8 para TMS. |

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.11+
* **Framework Web:** Streamlit
* **Tratamiento y Estructuración de Datos:** Pandas, OpenPyXL
* **Motor de Inteligencia Artificial:** Google GenAI SDK (`gemini-3.6-flash`)
* **Despliegue e Integración:** Streamlit Community Cloud (gestión segura mediante `st.secrets`)

---

## 🚀 Puesta en Marcha Local

### 1. Clonar el repositorio

`git clone [https://github.com/BlueLaserGo/limpiatext.git](https://github.com/BlueLaserGo/limpiatext.git)`

`cd limpiatext`

### 2. Instalar dependencias

`pip install -r requirements.txt`

### 3. Configurar variables de entorno (opcional)

Crea el archivo `.streamlit/secrets.toml` para almacenar tu clave de API:

`GEMINI_API_KEY = "tu_api_key_de_gemini"`

### 4. Ejecutar la aplicación

`streamlit run app.py`

---

## 👩‍💻 Autora

**Laura Serrano Gómez**

*Technical Writer | Functional Analyst | NLP & Localization Specialist*

* [LinkedIn](https://www.linkedin.com/in/lauserrano/)
