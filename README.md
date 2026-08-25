# 🧹 LimpiaText — UI Localization Engine

Herramienta de extracción y localización de cadenas de texto de interfaz de usuario (UI) a partir de Historias de Usuario exportadas de **Azure DevOps**.

Desarrollada en **Python (Streamlit)** e impulsada por **Google Gemini (`gemini-3.6-flash`)**.

---

## 🎯 Problema que resuelve
En proyectos de software gestionados con Azure DevOps, los requisitos de interfaz suelen estar redactados dentro de campos HTML enriquecidos junto a explicaciones funcionales y técnicas.

**LimpiaText** automatiza este proceso:
1. Depura el marcado HTML residual y comentarios internos.
2. Identifica y extrae de forma estructurada únicamente los elementos visibles de la UI (botones, campos, modales, alertas, selectores).
3. Permite la validación humana en vivo mediante tabla interactiva.
4. Genera traducciones especializadas a **Inglés**, **Catalán/Valenciano/Balear**, **Gallego** y **Euskera**.

---

## 🛠️ Arquitectura y Flujo
