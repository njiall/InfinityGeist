# TAR-01b — Chunking + canonical_rule_id

**Fase:** F1 (Ingesta de datos)  
**Prioridad:** 5 (crítica)  
**Estimación:** 6–8 h  
**Dependencia:** TAR-01 (extractor PDF → Markdown)  
**Estado:** ✅ Completado (2026-07-02)

---

## Objetivo original

Chunks semánticos por sección/subsección con ID que vincula el chunk ES↔EN de la misma regla. Esto define el techo de calidad de todo el sistema RAG.

---

## Enhanced

### Objetivo técnico

Implementar un pipeline de chunking que convierte Markdown procesado (de TAR-01) en chunks JSON-L estructurados, con:

1. **Chunks semánticos**: divididos por jerarquía de headings Markdown, ~200–400 tokens por chunk
2. **canonical_rule_id determinista**: derivado del manual + ruta de sección normalizada, permite vincular chunks ES↔EN de la misma regla
3. **Metadata preservada**: página de origen, ruta de sección, hash de contenido para deduplicación
4. **Detección de huérfanos**: reporte JSON de chunks sin par en el otro idioma
5. **Validación de comprensibilidad**: sampling manual confirma que chunks son autónomos

### Tareas atómicas completadas

1. ✅ **Definir modelo Pydantic Chunk** (30 min)
   - Ubicación: `shared/geist_shared/chunk_models.py`
   - Campos: `chunk_id` (UUID hex), `canonical_rule_id`, `lang`, `manual`, `section_path`, `page_start`, `page_end`, `content`, `content_hash`, `token_count`
   - Type hints completos, validación pydantic

2. ✅ **Algoritmo de chunking por heading** (2 h)
   - Ubicación: `ingestion/src/geist_ingestion/chunk.py`
   - Split recursivo por niveles Markdown (`#`, `##`, `###`, etc.)
   - Target 200–400 tokens por chunk (estimación con tiktoken)
   - Overlap 15–20% de tokens entre chunks adyacentes
   - Preserva tablas Markdown intactas

3. ✅ **Generación de canonical_rule_id determinista** (1 h)
   - Derivado de `manual_id` (core, anexo, etc.) + normalización de `section_path`
   - Normalización: lowercase, reemplaza espacios/puntuación por `_`, elimina caracteres especiales
   - Siglas técnicas preservadas: CAP, AVA, SWC, BS, PH, WIP, ARM, BTS, CC, ORO, KHD, etc.
   - Determinista: mismo Markdown → mismo canonical_rule_id siempre

4. ✅ **Script de chunking end-to-end** (1.5 h)
   - Entrada: `data/processed/{lang}/{manual}/content.md`
   - Salida: `data/chunks/{lang}/{manual}/chunks.jsonl` (una línea por chunk, JSON serializados)
   - Cálculo de `content_hash` SHA-256 por chunk para deduplicación
   - Conteo de tokens con tiktoken (modelo gpt-2)

5. ✅ **Reporte de chunks huérfanos** (1 h)
   - Script: `ingestion/src/geist_ingestion/validate.py`
   - Entrada: dos archivos `chunks.jsonl` (ES + EN)
   - Salida: `data/reports/{manual}/orphans.json`
   - Lista: canonical_rule_id sin par en el otro idioma + idioma donde falta
   - Reporte actual: 97 huérfanos detectados (48 ES, 49 EN) — requiere revisión manual

6. ✅ **Testing sampling manual** (1.5 h)
   - Sampling aleatorio: 20 chunks de ambos idiomas
   - Criterio: chunk comprensible aislado (sin contexto de párrafos anteriores)
   - Resultado: ≥18/20 pasan — chunks son semánticamente autónomos

### Dependencias

- **TAR-01**: Extractor PDF → Markdown (completado, produce `data/processed/{lang}/{manual}/content.md`)
- **TAR-00**: Bootstrap monorepo (completado)

### Riesgos / trade-offs

| Riesgo | Mitigación |
|--------|-----------|
| Chunks huérfanos sin par ES↔EN (97 actuales) | Reportados en `orphans.json`; revisión manual posterior; no bloquea MVP si son minoritarios |
| Thresholds token (200–400) demasiado restrictivos | Ajustables en `ingestion/chunk.py:CHUNK_TARGET_TOKENS`. Testeados vs distribución real de manuales. |
| Content hash collisions | Improbable con SHA-256; collision significa exacta duplicación — aceptable rechazar. |
| Siglas técnicas normalizadas mal | Whitelist explícita en `chunk.py:TECHNICAL_TERMS`. Extensible si falta alguna. |
| Serialización de Markdown con tablas | Preservadas como texto plano en `content`. Tests verifican no truncamiento. |

### Criterios de aceptación

- [x] Modelo `Chunk` en `shared/geist_shared/chunk_models.py` con mypy --strict válido
- [x] Script `ingestion/src/geist_ingestion/chunk.py` procesa ambos idiomas sin excepción
- [x] Output: `data/chunks/{lang}/{manual}/chunks.jsonl` con estructura esperada
  - Comprobación: 492 chunks ES, 445 chunks EN = 937 total
- [x] `canonical_rule_id` es determinista y vincula chunks ES↔EN de la misma regla
- [x] Reporte de huérfanos generado: `data/reports/core/orphans.json` (97 reglas sin par)
- [x] Sampling manual: 20 chunks aleatorios ≥18 comprensibles aislados ✓
- [x] mypy --strict pasa en ingestion/
- [x] Script ejecutable: `python -m geist_ingestion chunk --manual core --langs es en`

---

## Datos generados

**Ubicación:** `data/chunks/`

```
data/chunks/
├── es/
│   └── core/
│       └── chunks.jsonl          (492 chunks)
├── en/
│   └── core/
│       └── chunks.jsonl          (445 chunks)
└── reports/
    └── core/
        └── orphans.json          (97 reglas huérfanas)
```

**Estadísticas:**
- **Total chunks:** 937 (ES: 492, EN: 445)
- **Promedio tokens/chunk:** ~260 tokens
- **Tamaño on-disk:** ~1.2 MB (chunks.jsonl)
- **Tiempo generación:** <2 min en CPU moderna

**Ejemplo chunk (ES):**
```json
{
  "chunk_id": "554edae5adb3d792",
  "canonical_rule_id": "core::reglas_basicas",
  "lang": "es",
  "manual": "core",
  "section_path": "**REGLAS BÁSICAS**",
  "page_start": 1,
  "page_end": 1,
  "content": "Las reglas básicas son uno de los pilares de la mecánica general del juego...",
  "content_hash": "d5fcffdbcca42c54",
  "token_count": 397
}
```

---

## Siguiente paso

**TAR-02** (Indexación ChromaDB con embeddings multilingüe):
- Consume: `data/chunks/{lang}/{manual}/chunks.jsonl`
- Añade: modelo `intfloat/multilingual-e5-small` + prefijos "passage:" al indexar
- Output: ChromaDB persistente en `data/chroma/`
- Criterio de entrada: huérfanos documentados, no es bloqueante

