# ADR-002 — Extractor PDF: pymupdf4llm vs. alternativas (spike de licencia)

**Estado:** Aceptado  
**Fecha:** 2026-07-02  
**Contexto:** TAR-01 — antes de escribir una sola línea de ingesta

---

## Contexto

`pymupdf4llm` es la opción natural para convertir PDFs a Markdown estructurado para RAG.  
La duda es su licencia **AGPL-3.0**, que impone obligaciones de divulgación de código fuente
cuando el software se ejecuta como servicio de red.

---

## Hallazgos del spike (15 min)

### Qué implica AGPL-3.0

- Si un usuario interactúa con Geist vía red (API, bot Telegram), **AGPL exige publicar
  el código fuente completo** bajo términos compatibles con AGPL.
- La licencia comercial de Artifex (el fabricante) cuesta **$10.000–$50.000/año** — fuera
  de alcance para un proyecto no monetizado.
- **No hay restricción de uso personal o interno**: el trigger es la distribución en red.

### Situación concreta de Geist

| Factor | Valor |
|--------|-------|
| Proyecto monetizado | No |
| Código fuente publicado en GitHub | Sí (previsto) |
| Usuarios externos acceden a la API | Sí (bot Telegram) |
| Necesidad de código cerrado | No |

**Conclusión:** Al publicar el código en GitHub bajo una licencia compatible (MIT, Apache 2.0,
o la propia AGPL), Geist cumple automáticamente con los requisitos de AGPL. **El bloqueante
no existe para este proyecto.**

### Comparativa de alternativas

| Librería | Licencia | Calidad Markdown para LLM | Tablas | Velocidad |
|----------|----------|--------------------------|--------|-----------|
| **pymupdf4llm** | AGPL-3.0 | ★★★★★ | Buena | ★★★★★ |
| docling (IBM) | MIT | ★★★★☆ | ★★★★★ | ★★★ (requiere modelos ML) |
| pdfplumber | MIT | ★★☆☆☆ | ★★★☆ (solo tablas con bordes) | ★★★ |
| pypdf | MIT | ★★☆☆☆ | No | ★★★★★ |
| marker | GPL-3.0 | ★★★★☆ | Buena | ★★★ (requiere GPU) |

**Nota sobre docling:** mejor en tablas complejas y PDFs académicos/técnicos. Instalación
pesada (requiere modelos de ML descargados). Viable pero innecesariamente complejo para
PDFs nativos digitales como los manuales de Infinity N5.

---

## Decisión

**Usar `pymupdf4llm` (AGPL-3.0).**

Geist es open-source y no monetizado. Publicar el código en GitHub bajo MIT o AGPL-3.0
es suficiente para cumplir. La calidad de extracción de pymupdf4llm supera a las
alternativas sin requerir modelos ML adicionales — crítico para mantener el deploy simple.

### Condición: repositorio debe ser público

Esto no es negociable mientras se use pymupdf4llm. Si en el futuro:
- Se monetiza Geist, o
- Se necesita mantener el código cerrado

→ Migrar a **docling** (MIT) o adquirir licencia comercial de Artifex.

---

## Consecuencias

**Positivas:**
- Mejor calidad de extracción PDF → Markdown, sin coste adicional.
- Sin fricción legal para un proyecto open-source personal.
- Una dependencia menos pesada vs. docling (no requiere modelos ML).

**Negativas / trade-offs:**
- El repositorio **debe permanecer público** (GitHub). Código cerrado = violación de AGPL.
- Si Geist se convierte en producto comercial, hay que migrar el extractor o comprar licencia.
- AGPL puede entrar en conflicto con otras dependencias MIT si alguien hace un fork cerrado.

---

## Próximo paso

Descomentar `pymupdf4llm` en `ingestion/pyproject.toml` y comenzar TAR-01 (extractor).
