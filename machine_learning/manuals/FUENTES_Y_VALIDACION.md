# Estado y Procedencia de la Base de Conocimientos RAG

## 1. Declaración de Alcance y Metodología (Tesis)

El corpus técnico indexado en el subsistema RAG de CarBot (`machine_learning/manuals/`) constituye una **base de conocimiento técnico referencial y experimental**. 

- **Propósito**: Asistir al mecánico en la identificación de fallas y pasos de diagnóstico inicial durante el estudio experimental de tesis.
- **Estado de Validación**: `corpus_preliminar_taller`.
- **Condición de Uso**: No sustituye el manual de taller oficial del fabricante en reparaciones críticas o componentes de seguridad de alto voltaje. CarBot desacopla la confianza del clasificador ML de la similitud RAG y exige siempre la confirmación del técnico calificado.
- **Admisión operativa**: El índice FAISS carga exclusivamente los 85 fragmentos registrados en `metadatos_manuales.json`. Las guías web, síntomas y candidatos sin metadatos se excluyen del RAG operativo y solo pueden conservarse como material experimental.

---

## 2. Estructura y Fuentes por Marca

Los procedimientos están organizados en subcarpetas estructuradas:

1. **Toyota (`toyota/`)**:
   - Modelos: Yaris (2NR-FE), Prius HEV (2ZR-FXE), Corolla (2ZR-FE).
   - Publicaciones de Referencia: *Toyota Owner Workshop Manuals (Pub. RM0130E, RM3140U, RM2450U)*.
   - Portal Técnico Oficial: [Toyota Technical Information System (TIS)](https://techinfo.toyota.com).
2. **Nissan (`nissan/`)**:
   - Modelos: Sentra (MRA8DE / HR16DE), Versa (HR16DE).
   - Publicaciones de Referencia: *Nissan Service Manuals (SM20E00-B18, SM21E00-N17)*.
   - Portal Técnico Oficial: [Nissan Publications TechInfo](https://www.nissan-techinfo.com).
3. **Hyundai / Kia (`hyundai/`, `kia/`)**:
   - Modelos: Hyundai Accent (Gamma/Kappa 1.4/1.6L), Kia Rio (Gamma/Kappa).
   - Publicaciones de Referencia: *Hyundai Workshop Manual HMA-RB2019 / Kia Service Manual KMA-YB2020*.
   - Portales Oficiales: [Hyundai TechInfo](https://www.hyundaitechinfo.com) / [Kia Global Information System](https://www.kiatechinfo.com).
4. **Sistemas de Conversión GNV / GLP (`gnv_glp/`)**:
   - Sistemas: 5ta Generación Inyección Secuencial (Tomasetto Achille, STAG, Lovato).
   - Referencia: *Reglamento Técnico Automotriz MTC Perú y Guías Técnicas de Instalación de Gas*.
5. **Procedimientos Generales y Normas (`generales/`)**:
   - Normas: *SAE J1939 (Heavy Duty OBD), SAE J2012 (DTC Definitions), ISO 14229 (UDS)*.

---

## 3. Trazabilidad y Metadatos JSON

Cada fragmento indexado cuenta con registro en `metadatos_manuales.json`:
- `id_procedimiento`: Identificador unívoco (`RAG_PROC_001` a `RAG_PROC_064`).
- `archivo_fuente`: Ruta relativa exacta del archivo `.txt` existente en el repositorio.
- `sha256_fragmento`: Checksum SHA-256 criptográfico para verificar la integridad del texto.
- `codigos_dtc`: Lista normalizada de códigos OBD-II asociados.
- `manual_oem` / `url_referencia`: Categorización referencial estándar de manuales de taller para consulta técnica.
- `estado_validacion`: `corpus_preliminar_taller` con bandera de auditoría documental (requiere posterior firma y homologación en taller).

Las incorporaciones futuras requieren revisión documental, validación mecánica y actualización de su hash. Agregar un archivo `.txt` al directorio no provoca su indexación automática.
