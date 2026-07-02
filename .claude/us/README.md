# Tareas Geist — .claude/us/

Single source of truth para las tareas activas del proyecto.

## Nomenclatura

```
TAR-XX <Título descriptivo>.md
```

- `TAR-` prefijo fijo del proyecto (de "TARea")
- `XX` número de la tarea según el plan de desarrollo (TAR-00, TAR-01, TAR-01b, TAR-02...)
- `<Título descriptivo>` corto, en lenguaje natural, separado por espacios

Ejemplo: `TAR-02 Indexación embeddings multilingüe.md`

## Estructura del fichero

```markdown
# TAR-XX — <Título>

## Original
<descripción inicial de la tarea, según el plan de desarrollo>

## Enhanced
<versión enriquecida — añadida por /enrich-us; ausente hasta que se enriquezca>
```

`/enrich-us TAR-XX` localiza el fichero por prefijo, añade o reemplaza la sección `## Enhanced` y deja el resto intacto.

## Ciclo de vida

| Estado          | Ubicación              |
|-----------------|------------------------|
| En curso        | `.claude/us/`          |
| Archivada/Done  | `.claude/us/done/`     |

Al archivar (`/opsx:archive`), el fichero se mueve a `done/`.

## Secuencia MVP

```
F0: TAR-00 (✅ done)
F1: TAR-01, TAR-01b
F2: TAR-02, TAR-02b, TAR-03, TAR-03b, TAR-03c, TAR-03d, TAR-05, TAR-05b, TAR-09
F3: TAR-04
F5: TAR-08
```
