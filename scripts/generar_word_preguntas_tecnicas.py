"""
Script integral para compilar el documento Word (.docx) con todas las respuestas
técnicas exhaustivas para entrevistas con Líderes Técnicos y sustentación de Tesis.
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls


def create_full_document(output_path: str):
    doc = Document()

    # ---------------------------------------------------------
    # CONFIGURACIÓN DE PÁGINA Y MÁRGENES
    # ---------------------------------------------------------
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)

    # ---------------------------------------------------------
    # COLORES CORPORATIVOS Y ESTILOS
    # ---------------------------------------------------------
    COLOR_PRIMARY = RGBColor(27, 54, 93)  # Navy Profundo (#1B365D)
    COLOR_SECONDARY = RGBColor(75, 107, 148)  # Slate Azul (#4B6B94)
    COLOR_TEXT = RGBColor(44, 62, 80)  # Charcoal (#2C3E50)
    COLOR_MUTED = RGBColor(100, 116, 139)  # Gris suave (#64748B)

    # Estilo Normal
    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Arial"
    style_normal.font.size = Pt(10)
    style_normal.font.color.rgb = COLOR_TEXT
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(4)

    # ---------------------------------------------------------
    # FUNCIONES AUXILIARES DE FORMATEO
    # ---------------------------------------------------------
    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(
            f"<w:tcMar {nsdecls('w')}>"
            f'<w:top w:w="{top}" w:type="dxa"/>'
            f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'<w:left w:w="{left}" w:type="dxa"/>'
            f'<w:right w:w="{right}" w:type="dxa"/>'
            f"</w:tcMar>"
        )
        tcPr.append(tcMar)

    def set_cell_border(cell, **kwargs):
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = parse_xml(f"<w:tcBorders {nsdecls('w')}/>")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            edge_data = kwargs.get(edge)
            if edge_data:
                tag = f'<w:{edge} {nsdecls("w")} w:val="{edge_data.get("val", "single")}" w:sz="{edge_data.get("sz", "4")}" w:space="0" w:color="{edge_data.get("color", "auto")}"/>'
            else:
                tag = f'<w:{edge} {nsdecls("w")} w:val="none"/>'
            tcBorders.append(parse_xml(tag))
        tcPr.append(tcBorders)

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(11.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(10.5)
        run.font.bold = True
        run.font.color.rgb = COLOR_TEXT
        return p

    def add_p(text, bold_prefix="", italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.bold = True
            r_bold.font.color.rgb = COLOR_TEXT
        r_text = p.add_run(text)
        r_text.font.italic = italic
        return p

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.12
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.bold = True
            r_bold.font.color.rgb = COLOR_TEXT
        p.add_run(text)
        return p

    def add_callout(title, text, box_type="tip"):
        colors = {
            "tip": {
                "border": "1B365D",
                "bg": "F0F4F8",
                "title_color": RGBColor(27, 54, 93),
            },
            "important": {
                "border": "D97706",
                "bg": "FFFBEB",
                "title_color": RGBColor(180, 83, 9),
            },
            "success": {
                "border": "059669",
                "bg": "ECFDF5",
                "title_color": RGBColor(4, 120, 87),
            },
            "highlight": {
                "border": "4F46E5",
                "bg": "EEF2FF",
                "title_color": RGBColor(67, 56, 202),
            },
        }
        cfg = colors.get(box_type, colors["tip"])

        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        cell = table.cell(0, 0)
        cell.width = Inches(6.9)
        set_cell_background(cell, cfg["bg"])
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        set_cell_border(
            cell, left={"val": "single", "sz": "24", "color": cfg["border"]}
        )

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        run_title = p.add_run(f"📌 {title}\n")
        run_title.font.name = "Arial"
        run_title.font.size = Pt(10)
        run_title.font.bold = True
        run_title.font.color.rgb = cfg["title_color"]

        run_text = p.add_run(text)
        run_text.font.name = "Arial"
        run_text.font.size = Pt(9.5)
        run_text.font.color.rgb = RGBColor(51, 65, 85)

        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def add_code(code_text, caption=""):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        cell = table.cell(0, 0)
        cell.width = Inches(6.9)
        set_cell_background(cell, "1E293B")  # Slate oscuro
        set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
        set_cell_border(
            cell,
            top={"val": "single", "sz": "4", "color": "334155"},
            bottom={"val": "single", "sz": "4", "color": "334155"},
            left={"val": "single", "sz": "4", "color": "334155"},
            right={"val": "single", "sz": "4", "color": "334155"},
        )

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05

        run = p.add_run(code_text)
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(241, 245, 249)

        if caption:
            p_cap = doc.add_paragraph()
            p_cap.paragraph_format.space_before = Pt(1)
            p_cap.paragraph_format.space_after = Pt(4)
            p_cap.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r_cap = p_cap.add_run(f"Fragmento: {caption}")
            r_cap.font.name = "Arial"
            r_cap.font.size = Pt(8.0)
            r_cap.font.italic = True
            r_cap.font.color.rgb = COLOR_MUTED
        else:
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

    # ---------------------------------------------------------
    # PORTADA / ENCABEZADO PRINCIPAL
    # ---------------------------------------------------------
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(0)
    p_top.paragraph_format.space_after = Pt(2)
    r_tag = p_top.add_run(
        "GUÍA TÉCNICA MAESTRA PARA ENTREVISTA CON LÍDER TÉCNICO Y DEFENSA DE TESIS"
    )
    r_tag.font.name = "Arial"
    r_tag.font.size = Pt(9.5)
    r_tag.font.bold = True
    r_tag.font.color.rgb = COLOR_SECONDARY

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(2)
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run(
        "CarBot: Chatbot con Machine Learning, RAG y FastAPI para el Diagnóstico Vehicular"
    )
    r_title.font.name = "Arial"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_after = Pt(12)
    r_meta = p_meta.add_run(
        "Autor y Desarrollador Principal: Juan Joel Leon Chumbe | Coautora de Tesis: Luisa Leonor Poma Cataño\nLima, Perú — Año 2026 | Arquitectura Modular por Capas, DTOs, Custom Hooks & Resiliencia AI"
    )
    r_meta.font.size = Pt(9)
    r_meta.font.italic = True
    r_meta.font.color.rgb = COLOR_MUTED

    # Línea divisoria
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(8)
    r_div = p_div.add_run("―" * 58)
    r_div.font.color.rgb = RGBColor(203, 213, 225)
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ---------------------------------------------------------
    # BLOQUE 0: APORTE INDIVIDUAL Y ELEVATOR PITCH
    # ---------------------------------------------------------
    add_h1("BLOQUE 0: APORTE INDIVIDUAL, ROLES Y ELEVATOR PITCH")

    add_callout(
        "CLAVE DE ÉXITO ANTE UN LÍDER TÉCNICO",
        "Un líder técnico busca validar si realmente fuiste tú quien diseñó y programó el sistema o si fuiste un simple observador. "
        "Tu respuesta debe ser contundente: 'Yo fui el desarrollador de software e implementador de IA del proyecto. "
        "Construí el frontend en React/TypeScript, el backend en FastAPI con arquitectura modular por capas, los DTOs con Pydantic, "
        "los Custom Hooks, el clasificador ML con Calibrated SVM, el motor RAG con FAISS y la integración con WhatsApp y Gemini.' "
        "Tu compañera de tesis asumió el rol de investigación académica, redacción del informe y trabajo de campo.",
        "important",
    )

    add_h2(
        "Pregunta 0.1: ¿Qué desarrollé yo exactamente y qué hizo mi compañera de tesis?"
    )
    add_p(
        "Esta es la pregunta con mayor peso técnico y evaluativo. Para responder con total solvencia, "
        "se establece una matriz inequívoca de responsabilidades:"
    )

    # Tabla de Responsabilidades
    table_roles = doc.add_table(rows=1, cols=2)
    table_roles.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_roles.autofit = False

    hdr_cells = table_roles.rows[0].cells
    hdr_cells[0].width = Inches(3.45)
    hdr_cells[1].width = Inches(3.45)

    set_cell_background(hdr_cells[0], "1B365D")
    set_cell_background(hdr_cells[1], "475569")

    p0 = hdr_cells[0].paragraphs[0]
    r0 = p0.add_run(
        "Mi Aporte Individual: Juan Joel Leon Chumbe\n(Desarrollo de Software, Arquitectura & IA)"
    )
    r0.font.bold = True
    r0.font.color.rgb = RGBColor(255, 255, 255)
    r0.font.size = Pt(9.5)

    p1 = hdr_cells[1].paragraphs[0]
    r1 = p1.add_run(
        "Aporte de mi Compañera: Luisa Leonor Poma\n(Investigación Académica & Trabajo de Campo)"
    )
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(255, 255, 255)
    r1.font.size = Pt(9.5)

    roles_data = [
        (
            "Arquitectura Backend Completa",
            "Diseño e implementación de FastAPI bajo arquitectura limpia modular por capas (Interfaces, Core de Dominio, Infraestructura y Repositorios).",
            "Marco Teórico & Metodología",
            "Redacción de los capítulos metodológicos, marco teórico, antecedentes nacionales e internacionales en la tesis.",
        ),
        (
            "Frontend & Custom Hooks",
            "Desarrollo completo de la SPA en React 19 + TypeScript con Vite, creando componentes modulares y Custom Hooks ('useDiagnosticos', 'useMecanicos', 'useMetricas').",
            "Levantamiento de Campo en Carabayllo",
            "Coordinación con los talleres mecánicos para la toma de tiempos tradicionales (pre-test) y encuestas de satisfacción.",
        ),
        (
            "Modelado y DTOs Fuertemente Tipados",
            "Definición de DTOs con Pydantic v2 en backend e interfaces TypeScript en frontend para blindar contratos de datos de entrada/salida.",
            "Fichas de Recolección de Datos",
            "Diseño y aplicación de las fichas físicas/digitales de recolección de sintomatología e instrumentos de medición O1 y O2.",
        ),
        (
            "Machine Learning & RAG con FAISS",
            "Entrenamiento, comparación y serialización del modelo Calibrated Linear SVM; implementación del motor RAG con FAISS e indexación vectorial.",
            "Consolidación Documental",
            "Recopilación de manuales automotrices en PDF y apoyo en la redacción de anexos y referencias bibliográficas.",
        ),
        (
            "Integración Meta WhatsApp & Gemini",
            "Desarrollo del Webhook con verificación HMAC, cola de reintentos y Rate Limiter distribuido (Token Bucket) para cuotas de LLM.",
            "Tabulación de Resultados",
            "Apoyo en la tabulación estadística de datos recolectados para los gráficos descriptivos del informe de tesis.",
        ),
        (
            "Persistencia & Test Suite",
            "Modelado relacional en PostgreSQL con SQLAlchemy Async, migraciones Alembic y creación de más de 30 suites de pruebas en Pytest.",
            "Sustentación de Justificación Social",
            "Defensa de la justificación económica, social y operativa de los talleres mecánicos de la zona norte de Lima.",
        ),
    ]

    for item in roles_data:
        row = table_roles.add_row()
        c0, c1 = row.cells[0], row.cells[1]
        c0.width, c1.width = Inches(3.45), Inches(3.45)
        set_cell_margins(c0, top=70, bottom=70, left=100, right=100)
        set_cell_margins(c1, top=70, bottom=70, left=100, right=100)
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_border(
            c0,
            bottom={"val": "single", "sz": "4", "color": "E2E8F0"},
            right={"val": "single", "sz": "4", "color": "E2E8F0"},
        )
        set_cell_border(c1, bottom={"val": "single", "sz": "4", "color": "E2E8F0"})

        pc0 = c0.paragraphs[0]
        pc0.add_run(f"• {item[0]}: ").font.bold = True
        pc0.add_run(item[1]).font.size = Pt(8.5)

        pc1 = c1.paragraphs[0]
        pc1.add_run(f"• {item[2]}: ").font.bold = True
        pc1.add_run(item[3]).font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_h2("Pregunta 0.2: ¿Cuál es el Elevator Pitch técnico de CarBot en 60 segundos?")
    add_p(
        "«CarBot es un sistema de diagnóstico vehicular híbrido multimodal diseñado para resolver la ambigüedad en la recepción de vehículos en talleres mecánicos. "
        "A diferencia de un chatbot genérico que alucina especificaciones técnicas, CarBot combina tres capas coordinadas: "
        "(1) Un clasificador de Machine Learning supervisado (Calibrated Linear SVM) que procesa texto coloquial y señales FFT de audio en milisegundos; "
        "(2) Un motor RAG basado en FAISS que recupera procedimientos exactos desde manuales de taller indexados; y "
        "(3) Un LLM (Google Gemini) que actúa exclusivamente como capa explicativa bajo 'grounding' estricto. "
        "Todo está orquestado con FastAPI asíncrono, DTOs de Pydantic, PostgreSQL y un panel reactivo en React 19 con TypeScript.»"
    )

    add_h2("Pregunta 0.3: ¿Qué decisiones técnicas tomaste tú de forma autónoma?")
    add_bullet(
        "Decisión 1: Separar la inferencia en ML + RAG antes de llamar al LLM. Esto redujo el costo de tokens en un 70% y garantiza que el sistema siga funcionando en modo degradado si la API de Gemini sufre un corte de servicio.",
        "Inferencia Determinística Híbrida: ",
    )
    add_bullet(
        "Decisión 2: Utilizar DTOs inmutables con Pydantic v2 en el Backend e interfaces TypeScript espejo en el Frontend, evitando inconsistencias de datos y validando tipos en tiempo de compilación y ejecución.",
        "Contratos de Datos Estrictos (DTOs): ",
    )
    add_bullet(
        "Decisión 3: Implementar un Rate Limiter con Token Bucket y cola persistente ('trabajos_gemini' en PostgreSQL) para absorber picos de tráfico en WhatsApp y nunca perder peticiones por límites de cuota 429 de la API.",
        "Resiliencia contra Throttling de APIs: ",
    )
    add_bullet(
        "Decisión 4: Arquitectura de Custom Hooks ('useDiagnosticos', 'useMecanicos', 'useMetricas') en React para desacoplar completamente la capa de presentación de la capa de transporte HTTP.",
        "Frontend Desacoplado: ",
    )

    # ---------------------------------------------------------
    # BLOQUE 1: LENGUAJE, ARQUITECTURA Y ORGANIZACIÓN
    # ---------------------------------------------------------
    add_h1("BLOQUE 1: LENGUAJE, ARQUITECTURA Y ORGANIZACIÓN DEL PROYECTO")

    add_h2("Pregunta 1: ¿Por qué eligieron Python?")
    add_p(
        "La elección de Python obedeció a cuatro factores arquitectónicos y de ingeniería:"
    )
    add_bullet(
        "Python es el estándar de la industria. Permitió utilizar scikit-learn, FAISS, SciPy (para FFT de audios), NumPy y Pandas dentro del mismo ecosistema, sin necesidad de recurrir a microservicios externos o puentes entre lenguajes (ej. Node.js llamando a scripts en Python).",
        "1. Ecosistema de Machine Learning y Procesamiento de Señales: ",
    )
    add_bullet(
        "FastAPI es un framework moderno basado en ASGI (Starlette y Uvicorn) que ofrece rendimiento comparable a Node.js o Go gracias a uvloop y concurrencia asíncrona nativa ('async' / 'await'), ideal para webhooks de WhatsApp con alta concurrencia.",
        "2. Rendimiento Asíncrono de FastAPI: ",
    )
    add_bullet(
        "FastAPI utiliza Pydantic v2 (escrito en Rust) para serialización ultrarrápida, validación de esquemas JSON y generación automática de contratos OpenAPI / Swagger.",
        "3. Tipado Estricto y Validación con Pydantic: ",
    )
    add_bullet(
        "Permitió serializar modelos entrenados (.pkl con joblib) y cargarlos en memoria compartida al inicio de la aplicación en milisegundos mediante inyección de dependencias (Singleton).",
        "4. Carga In-Memory de Modelos:",
    )

    add_h2(
        "Pregunta 2: ¿Cómo está estructurado el proyecto y por qué eligieron una arquitectura modular por capas?"
    )
    add_p(
        "El proyecto sigue una Arquitectura Modular por Capas (Clean Architecture / Hexagonal). "
        "Esto separa estrictamente las responsabilidades, facilita las pruebas unitarias y permite cambiar tecnologías sin reescribir la lógica del negocio."
    )

    add_code(
        """backend/
├── src/
│   ├── interfaces/api/v1/       # CAPA 1: Controladores & Endpoints REST y Webhooks
│   │   ├── endpoints/          # Rutas (/diagnostico, /webhook, /mecanicos, /metricas)
│   │   ├── router.py           # Agrupador central de rutas API v1
│   │   └── schemas.py          # DTOs Pydantic (SymptomRequestDTO, DiagnosticResponseDTO)
│   ├── core/                   # CAPA 2: Lógica de Dominio y Servicios de Negocio
│   │   ├── gestor_diagnostico.py   # Orquestador del pipeline de diagnóstico
│   │   ├── audio_processor.py      # FFT, normalización RMS y análisis acústico
│   │   ├── gemini_queue.py         # Rate limiter, Token Bucket y cola de reintentos
│   │   ├── traductor_jerga.py      # Normalizador léxico de modismos peruanos
│   │   ├── session_manager.py      # Estado conversacional en memoria/Redis
│   │   ├── sanitizer.py            # Protección contra Prompt Injection y caracteres extraños
│   │   └── security.py             # Hasheo de teléfonos (Habeas Data) y JWT
│   └── infrastructure/         # CAPA 3: Persistencia y Adaptadores Externos
│       ├── database/           # Modelos SQLAlchemy Async, repositorios y conexiones
│       ├── modelo_ml.py        # Adaptador del clasificador supervisado (joblib)
│       ├── motor_rag.py        # Adaptador de búsqueda vectorial con FAISS
│       └── aws_secrets.py      # Integración con AWS Secrets Manager / .env
frontend/                       # SPA React 19 + TypeScript + Vite
├── src/
│   ├── services/api.ts         # Capa de transporte HTTP (Axios / Fetch tipado)
│   ├── hooks/                  # Custom Hooks (useDiagnosticos, useMecanicos, useMetricas)
│   ├── components/             # Componentes UI modulares (Dashboard, Simulador, etc.)
│   └── types/                  # Modelos TypeScript sincronizados con los DTOs
machine_learning/               # Entorno aislado de Ciencia de Datos
├── data/                       # Datasets curados y sintéticos aumentados
├── manuals/                    # Corpus técnico de manuales OEM indexables por RAG
├── models/                     # Modelos serializados (.pkl) y métricas de desempeño
└── training/                   # Scripts de entrenamiento, validación cruzada y evaluación""",
        caption="Estructura Monorepo Desacoplada de CarBot",
    )

    add_h2("Pregunta 3: ¿Qué ventajas aportan los DTOs y los Custom Hooks?")
    add_p(
        "• DTOs (Data Transfer Objects con Pydantic): ",
        bold_prefix="Beneficios de los DTOs: ",
    )
    add_bullet(
        "Validación en la frontera: Garantizan que datos corruptos, incompletos o mal formateados sean rechazados con un HTTP 422 antes de llegar a la lógica de negocio o a los modelos de IA."
    )
    add_bullet(
        "Inmutabilidad y seguridad de tipos: Previenen condiciones de carrera y aseguran que cada petición tenga un objeto de entrada y salida independiente con campos tipados (int, str, float)."
    )
    add_bullet(
        "Documentación viviente: Generan automáticamente el esquema JSON Schema y Swagger UI para el equipo de desarrollo."
    )

    add_p(
        "• Custom Hooks en React (useDiagnosticos, useMecanicos, useMetricas): ",
        bold_prefix="Beneficios de los Hooks: ",
    )
    add_bullet(
        "Separación de Conceptos: Los componentes de UI solo renderizan; no saben cómo se llama al backend ni cómo se maneja el estado de carga (loading), error o paginación."
    )
    add_bullet(
        "Reutilización de Lógica: El mismo hook 'useDiagnosticos' es consumido por la vista de auditoría del administrador y por el simulador interactivo de pruebas."
    )

    add_h2("Pregunta 4: ¿Qué librerías y dependencias usa cada parte del sistema?")

    # Tabla de librerías
    table_libs = doc.add_table(rows=1, cols=3)
    table_libs.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_libs.autofit = False

    c_hdr = table_libs.rows[0].cells
    c_hdr[0].width = Inches(1.8)
    c_hdr[1].width = Inches(2.2)
    c_hdr[2].width = Inches(2.9)

    set_cell_background(c_hdr[0], "1B365D")
    set_cell_background(c_hdr[1], "1B365D")
    set_cell_background(c_hdr[2], "1B365D")

    for idx, text in enumerate(["Capa", "Librería / Herramienta", "Propósito Técnico"]):
        p = c_hdr[idx].paragraphs[0]
        r = p.add_run(text)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9)

    libs_info = [
        (
            "Backend Web",
            "FastAPI (0.141) + Uvicorn",
            "Servidor ASGI asíncrono de alto rendimiento para API REST y Webhooks.",
        ),
        (
            "Validación",
            "Pydantic v2 (2.13)",
            "Definición y serialización de DTOs y validación de esquemas de datos.",
        ),
        (
            "Machine Learning",
            "scikit-learn + joblib + NumPy",
            "Pipeline TF-IDF, clasificación supervisada Calibrated Linear SVM y serialización.",
        ),
        (
            "Vector Search / RAG",
            "faiss-cpu (1.15)",
            "Indexación y búsqueda de similitud coseno ultrarrápida en memoria.",
        ),
        (
            "Procesamiento Señales",
            "SciPy (scipy.fft)",
            "Transformada Rápida de Fourier y normalización de audio de WhatsApp.",
        ),
        (
            "Persistencia",
            "SQLAlchemy 2.0 (asyncio) + asyncpg",
            "ORM asíncrono y driver de alto rendimiento para PostgreSQL.",
        ),
        (
            "Migraciones BD",
            "Alembic (1.19)",
            "Control de versiones del esquema de base de datos y migraciones.",
        ),
        (
            "Seguridad",
            "PyJWT + cryptography (PBKDF2/Fernet)",
            "Autenticación JWT para admin y pseudonimización segura de números telefónicos.",
        ),
        (
            "Rate Limiting",
            "slowapi + redis + limits",
            "Protección contra saturación en endpoints REST y control de cuotas de tokens.",
        ),
        (
            "Frontend Core",
            "React 19 + TypeScript 6 + Vite 8",
            "Single Page Application fuertemente tipada con empaquetado optimizado.",
        ),
        (
            "UI & Gráficos",
            "Lucide React + Recharts",
            "Iconografía moderna y componentes de visualización gráfica interactiva.",
        ),
        (
            "Testing & Calidad",
            "Pytest + pytest-asyncio + Oxlint",
            "Suite de pruebas unitarias/integración y linter de alto rendimiento.",
        ),
    ]

    for item in libs_info:
        row = table_libs.add_row()
        c0, c1, c2 = row.cells[0], row.cells[1], row.cells[2]
        c0.width, c1.width, c2.width = Inches(1.8), Inches(2.2), Inches(2.9)
        set_cell_margins(c0, top=60, bottom=60, left=80, right=80)
        set_cell_margins(c1, top=60, bottom=60, left=80, right=80)
        set_cell_margins(c2, top=60, bottom=60, left=80, right=80)
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_background(c2, "FFFFFF")
        set_cell_border(c0, bottom={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_border(c1, bottom={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_border(c2, bottom={"val": "single", "sz": "4", "color": "E2E8F0"})

        c0.paragraphs[0].add_run(item[0]).font.bold = True
        c1.paragraphs[0].add_run(item[1]).font.size = Pt(8.5)
        c2.paragraphs[0].add_run(item[2]).font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ---------------------------------------------------------
    # BLOQUE 2: FLUJO DE PETICIONES DE INICIO A FIN
    # ---------------------------------------------------------
    add_h1("BLOQUE 2: FLUJO DE EJECUCIÓN END-TO-END Y PROCESAMIENTO")

    add_h2("Pregunta 5: ¿Cómo fluye una petición de inicio a fin?")
    add_p(
        "El ciclo de vida de una consulta sigue un flujo estrictamente orquestado de 9 pasos:"
    )
    add_bullet(
        "1. Recepción en Webhook: Meta Cloud API envía una solicitud HTTP POST al endpoint '/api/v1/webhook/whatsapp'.",
        "Paso 1: ",
    )
    add_bullet(
        "2. Validación de Seguridad & Firma: Se valida la firma digital HMAC SHA-256 en el encabezado 'X-Hub-Signature-256'.",
        "Paso 2: ",
    )
    add_bullet(
        "3. Pseudonimización & Control de Roles: El número telefónico es transformado mediante hash criptográfico (Habeas Data). Se consulta el rol en PostgreSQL: si es Cliente, se le devuelve el menú de servicios; si es Mecánico Autorizado, entra al motor de diagnóstico.",
        "Paso 3: ",
    )
    add_bullet(
        "4. Preprocesamiento Multimodal: Si el mensaje es audio, 'AudioProcessor' descarga el binario, calcula RMS para filtrar silencios y extrae la frecuencia dominante con FFT. Si es texto, 'Sanitizer' elimina caracteres sospechosos y 'TraductorJerga' estandariza modismos peruanos.",
        "Paso 4: ",
    )
    add_bullet(
        "5. Clasificación Machine Learning: El síntoma normalizado se transforma en vector numérico con TF-IDF y el modelo Calibrated Linear SVM predice la falla más probable y su probabilidad calibrada (0 a 100%).",
        "Paso 5: ",
    )
    add_bullet(
        "6. Recuperación RAG: 'MotorRAG' expande la consulta con códigos OBD-II/DTC, genera el vector TF-IDF, lo normaliza L2 y realiza búsqueda en FAISS ('IndexFlatIP'), recuperando el procedimiento técnico exacto y su similitud de coseno.",
        "Paso 6: ",
    )
    add_bullet(
        "7. Síntesis Controlada con Gemini (XAI): Se valida la cuota en el 'GeminiRateLimiter'. Si hay disponibilidad, se envía el prompt ensamblado (Grounding estricto: Síntoma + Predicción ML + Manual RAG). Si Gemini falla o supera la cuota (429), entra el fallback determinístico ML+RAG sin caerse.",
        "Paso 7: ",
    )
    add_bullet(
        "8. Persistencia y Trazabilidad: Se registra el diagnóstico en PostgreSQL ('diagnosticos', 'trazas_ejecucion', métricas de tokens y latencias) mediante SQLAlchemy asíncrono.",
        "Paso 8: ",
    )
    add_bullet(
        "9. Respuesta al Usuario: Se envía el mensaje formateado de vuelta al WhatsApp del mecánico vía Meta Graph API.",
        "Paso 9: ",
    )

    add_h2("Pregunta 6: ¿Cómo se maneja la diferenciación de roles en WhatsApp?")
    add_bullet(
        "Cliente Común: No tiene acceso al motor de IA ni a diagnósticos técnicos. Recibe un menú informativo con horarios, servicios y ubicación. Si marca la opción 4, genera una 'Solicitud de Acceso Mecánico'.",
        "Rol Cliente: ",
    )
    add_bullet(
        "Mecánico Autorizado: Autorizado por el Administrador. Puede ingresar síntomas en lenguaje natural o audios de motor y recibir diagnósticos preliminares completos con procedimientos técnicos.",
        "Rol Mecánico: ",
    )
    add_bullet(
        "Administrador del Taller: Es el único usuario con credenciales para iniciar sesión en el panel web React. Puede autorizar mecánicos, auditar diagnósticos, validar resultados y supervisar métricas.",
        "Rol Administrador: ",
    )

    add_h2("Pregunta 7: ¿Cómo funciona el procesamiento de audios de motor?")
    add_p(
        "El módulo 'AudioProcessor' implementa análisis acústico mediante procesamiento digital de señales:"
    )
    add_bullet(
        "Normalización de Amplitud: Se divide la señal entre su valor absoluto máximo (x(t) / max(|x(t)|)), nivelando el volumen sin importar la distancia del micrófono al motor."
    )
    add_bullet(
        "Detección de Silencio mediante Energía RMS: Se calcula el valor cuadrático medio. Si la energía es inferior a 0.01, se descarta el audio y se pide al mecánico volver a grabar."
    )
    add_bullet(
        "Transformada Rápida de Fourier (FFT): Transforma el audio del dominio del tiempo al dominio de la frecuencia, identificando los picos en Hertz (ej. chillidos de faja o pastillas en >2500 Hz vs golpeteos mecánicos en <800 Hz)."
    )

    # ---------------------------------------------------------
    # BLOQUE 3: MACHINE LEARNING, RAG Y GEMINI
    # ---------------------------------------------------------
    add_h1("BLOQUE 3: MACHINE LEARNING, RAG Y SÍNTESIS CON GEMINI")

    add_h2("Pregunta 8: ¿Cómo interactúan Machine Learning, RAG y Gemini entre sí?")
    add_p(
        "La interacción se basa en el principio de Inteligencia Artificial Explicable (Explainable AI - XAI) y Arquitectura Híbrida:"
    )

    add_code(
        """                     [ ENTRADA: WhatsApp (Texto / Audio FFT) ]
                                      |
                    +-----------------+-----------------+
                    |                                   |
                    v                                   v
      [ 1. CLASIFICADOR ML ]                  [ 2. MOTOR RAG FAISS ]
  - Vectorizador TF-IDF (1,2 n-gramas)    - Expansión de consulta + DTC
  - Modelo Calibrated Linear SVM          - Búsqueda vectorial en IndexFlatIP
  - Inferencia física sub-15ms            - Recupera procedimiento de manual OEM
  - Salida: Clase Falla + Probabilidad    - Salida: Texto Procedimiento + Similitud %
                    |                                   |
                    +-----------------+-----------------+
                                      |
                                      v
                        [ 3. SÍNTESIS CON GEMINI ]
    Prompt con Grounding Estricto: Sintoma + Falla ML + Procedimiento RAG
    -> Genera respuesta explicativa estructurada (3 secciones obligatorias)
    -> En caso de fallo de API / 429: Fallback determinístico directo""",
        caption="Interacción Híbrida: ML (Enrutador) + RAG (Verdad Técnica) + LLM (Explicador)",
    )

    add_h2("Pregunta 9: ¿Cómo está implementado el RAG exactamente y qué fuentes usa?")
    add_p(
        "• Algoritmo de Indexación y Búsqueda: ",
        bold_prefix="Implementación Técnica del RAG: ",
    )
    add_bullet(
        "Indexación de Documentos: Se parsean los manuales técnicos divididos por delimitadores de sección ('=== TITULO ==='). Se genera una huella criptográfica SHA-256 por cada procedimiento para evitar duplicados."
    )
    add_bullet(
        "Vectorización: Se utiliza 'TfidfVectorizer' configurado con 'sublinear_tf=True', n-gramas (1, 2) y un diccionario especializado de 'stop words' automotrices."
    )
    add_bullet(
        "Índice FAISS: La matriz resultante se normaliza mediante norma L2 ('faiss.normalize_L2') y se indexa en un 'faiss.IndexFlatIP' (Inner Product), haciendo que el producto interno coincida exactamente con la similitud de coseno en tiempo constante O(1)."
    )
    add_bullet(
        "Expansión de Consultas: Se incluye un diccionario de expansión semántica que traduce términos populares y códigos DTC (ej. 'cascabeleo' -> 'p0300 misfire bujias encendido')."
    )

    add_p(
        "• Fuentes de Información Utilizadas: ",
        bold_prefix="Corpus de Conocimiento Técnico: ",
    )
    add_bullet(
        "Manuales de servicio y procedimientos de taller para marcas comunes en el mercado peruano (Toyota, Nissan, Hyundai, Kia, Chevrolet)."
    )
    add_bullet(
        "Fichas técnicas de procedimientos de taller de Carabayllo con especificaciones de torques, ajustes de válvulas, purga de frenos, inyección diésel Common Rail y sistemas a gas GNV/GLP."
    )

    add_h2(
        "Pregunta 10: ¿Por qué eligieron TF-IDF + Linear SVM en lugar de un LLM puro o Deep Learning?"
    )
    add_bullet(
        "Cero Alucinación en la Clasificación: Un clasificador supervisado siempre mapea estrictamente a una de las categorías taxonómicas del taller, sin inventar nombres de componentes.",
        "1. Determinismo y Confiabilidad: ",
    )
    add_bullet(
        "Linear SVM con TF-IDF procesa una inferencia en menos de 10 milisegundos en una CPU modesta, sin requerir GPUs costosas ni servidores de inferencia pesados.",
        "2. Eficiencia y Baja Latencia: ",
    )
    add_bullet(
        "Un Linear SVM con regularización L2 evita el sobreajuste (overfitting) en datasets de texto de tamaño acotado (cientos a miles de muestras), donde redes neuronales profundas (BERT/LLMs) sufrirían sobreajuste severo.",
        "3. Desempeño en Datasets Acotados: ",
    )
    add_bullet(
        "Permite calibrar probabilidades con 'CalibratedClassifierCV', entregando un valor matemático real de confianza para activar el flag 'requiere_revision_humana'.",
        "4. Calibración de Probabilidad:",
    )

    add_h2("Pregunta 11: ¿Cómo se entrena el modelo y cada cuánto se reentrena?")
    add_p(
        "El entrenamiento se ejecuta mediante el script 'entrenar_y_comparar_modelos.py' bajo una metodología rigurosa:"
    )
    add_bullet(
        "Validación Cruzada Estratificada: Se usa 'StratifiedKFold(n_splits=5)' para asegurar que todas las categorías de falla estén representadas proporcionalmente en cada partición."
    )
    add_bullet(
        "Comparación de Algoritmos: Se evalúan MultinomialNB, LogisticRegression, RandomForest y LinearSVC. LinearSVC calibrado obtuvo de manera consistente el F1-Score más alto (>0.98) y el menor error de calibración."
    )
    add_bullet(
        "Frecuencia de Reentrenamiento: Se aplica un enfoque de Reentrenamiento Programado por Lotes (Batch Retraining). No se reentrena en caliente para evitar deriva catastrófica. Se reentrena mensualmente o cuando se acumulan nuevos diagnósticos validados por los mecánicos en PostgreSQL."
    )

    add_h2("Pregunta 12: ¿Cómo manejan nuevas fallas o nuevos modelos vehiculares?")
    add_p(
        "La arquitectura desacoplada resuelve esto en 3 niveles sin requerir reentrenamientos inmediatos:"
    )
    add_bullet(
        "Nivel 1 - Ingesta RAG Inmediata: Si llega un vehículo nuevo o un procedimiento inédito, solo se agrega el texto en 'machine_learning/manuals/'. El motor RAG lo indexa automáticamente al arrancar. Gemini ya podrá responder con ese manual de inmediato.",
        "1. Actualización RAG sin Código: ",
    )
    add_bullet(
        "Nivel 2 - Extensión de Taxonomía: Se pueden agregar nuevas clases y códigos DTC en 'catalogo_fallas.py'.",
        "2. Catálogo Modular: ",
    )
    add_bullet(
        "Nivel 3 - Feedback Loop: Los diagnósticos marcados con correcciones por el mecánico en el panel web se exportan como nuevo lote de entrenamiento para la siguiente versión del modelo ML.",
        "3. Aprendizaje Activo: ",
    )

    add_h2("Pregunta 13: ¿Qué pasa si el modelo se equivoca?")
    add_bullet(
        "Detección de Baja Confianza: Si la probabilidad calibrada cae por debajo del umbral (ej. <60%), el sistema activa 'requiere_revision_humana = True' y notifica al usuario que se requiere inspección física directa.",
        "1. Flag de Revisión Humana: ",
    )
    add_bullet(
        "Prompt Guardrails en Gemini: El modelo generativo tiene la instrucción explícita de NO contradecir el manual ni inventar diagnósticos si la similitud RAG es baja.",
        "2. Restricciones de Generación: ",
    )
    add_bullet(
        "Prioridad de Seguridad: Ante cualquier síntoma crítico (frenos, fuga de combustible, recalentamiento severo), el bot emite una alerta de seguridad preventiva recomendando apagar el motor y remolcar el vehículo.",
        "3. Protocolo de Seguridad: ",
    )
    add_bullet(
        "Validación Administrativa: Desde el panel web, el administrador puede corregir la etiqueta de la falla para alimentar el dataset de reentrenamiento.",
        "4. Corrección en Panel: ",
    )

    # ---------------------------------------------------------
    # BLOQUE 4: GESTIÓN DE APIs, RESILIENCIA Y SEGURIDAD
    # ---------------------------------------------------------
    add_h1("BLOQUE 4: GESTIÓN DE APIs, RESILIENCIA Y SEGURIDAD")

    add_h2("Pregunta 14: ¿Cómo gestionan las claves de la API y los secretos?")
    add_bullet(
        "Carga Segura con Pydantic Settings: Se utiliza 'src/config.py' que valida la existencia de variables de entorno tipadas mediante '.env' o variables del sistema operativo.",
        "1. Configuración Centralizada: ",
    )
    add_bullet(
        "Soporte AWS Secrets Manager: El módulo 'src/infrastructure/aws_secrets.py' permite recuperar las credenciales directamente desde la nube de AWS en entornos productivos.",
        "2. Bóveda Cloud: ",
    )
    add_bullet(
        "Fail-Safe en Arranque: Si falta la clave de Gemini, el sistema inicia en modo 'degradación segura', permitiendo que el servidor funcione con diagnósticos locales basados en ML y RAG sin crashear.",
        "3. Tolerancia a Fallos: ",
    )

    add_h2(
        "Pregunta 15: ¿Cómo gestionan los errores y el límite de cuota (Rate Limit 429) de Gemini?"
    )
    add_p(
        "Se implementó un sistema de resiliencia de nivel empresarial en 'gemini_queue.py':"
    )
    add_bullet(
        "Token Bucket & Rate Limiter: Limita las llamadas a 15 RPM (Requests Per Minute) y calcula los tokens por minuto para evitar sobrepasar la cuota gratuita de Google Gemini.",
        "1. Algoritmo Token Bucket: ",
    )
    add_bullet(
        "Cola de Solicitudes Persistente ('trabajos_gemini'): Si la cuota está copada, la solicitud se encola en PostgreSQL con estado 'pendiente', asignando un tiempo estimado de espera y procesándose de forma asíncrona.",
        "2. Cola Asíncrona: ",
    )
    add_bullet(
        "Retries con Exponential Backoff & Jitter: En caso de error de red o 429, se reintenta automáticamente respetando el encabezado 'Retry-After' del servidor de Google.",
        "3. Reintentos Exponenciales: ",
    )
    add_bullet(
        "Degradación Elegante (Graceful Degradation): Si la API de Gemini no responde en el tiempo límite (timeout de 10s), el orquestador no devuelve un error al mecánico; ensambla inmediatamente una respuesta técnica utilizando el resultado del modelo ML y el texto del RAG.",
        "4. Fallback Determinístico: ",
    )

    add_h2("Pregunta 16: ¿Qué optimizaciones de rendimiento implementaron?")
    add_bullet(
        "Cache en Memoria ('DiagnosticCache'): Respuestas cacheadas con TTL para consultas frecuentes e idénticas, reduciendo la latencia de 1800ms a menos de 5ms.",
        "1. Caché de Diagnósticos: ",
    )
    add_bullet(
        "FAISS Inner Product L2: Búsqueda de similitud vectorial en tiempo submilisegundo sobre vectores TF-IDF.",
        "2. Optimización Vectorial: ",
    )
    add_bullet(
        "Pool de Conexiones Asíncronas: SQLAlchemy Async con driver 'asyncpg', manteniendo el uso de memoria RAM por debajo de 150 MB bajo carga concurrente.",
        "3. Asincronía Total: ",
    )
    add_bullet(
        "Frontend con Vite & Tree-Shaking: Empaquetado mínimo, renderizado optimizado con Custom Hooks y CSS Vanilla sin la sobrecarga de dependencias pesadas.",
        "4. Frontend Ligero: ",
    )

    add_h2("Pregunta 17: ¿Cómo garantizan la privacidad de datos (Habeas Data)?")
    add_p(
        "En cumplimiento con la Ley de Protección de Datos Personales (Ley N° 29733 - Perú) y estándares GDPR:"
    )
    add_bullet(
        "Pseudonimización Criptográfica: Los números telefónicos nunca se guardan en texto plano en los registros de diagnóstico de la tesis; se almacenan como hashes criptográficos HMAC con sal secreta.",
        "1. Hashing con Sal: ",
    )
    add_bullet(
        "Sanitización de Prompts: Se remueven DNIs, placas vehiculares y nombres propios antes de enviar el texto al modelo fundacional externo de Gemini.",
        "2. Sanitizador PII: ",
    )

    # ---------------------------------------------------------
    # BLOQUE 5: TESTING, MÉTRICAS Y DESAFÍOS TÉCNICOS
    # ---------------------------------------------------------
    add_h1("BLOQUE 5: TESTING, MÉTRICAS Y DESAFÍOS TÉCNICOS")

    add_h2("Pregunta 18: ¿Qué pruebas automatizadas hicieron?")
    add_p(
        "Se implementó una suite integral de más de 34 archivos de test en 'backend/tests/' con Pytest:"
    )
    add_bullet(
        "Pruebas Unitarias: Validación de esquemas DTO con Pydantic, algoritmos de jerga, sanitizer, hashing y transformadas FFT.",
        "1. Unit Tests: ",
    )
    add_bullet(
        "Pruebas de Integración: Endpoints FastAPI ('TestClient'), autenticación JWT, persistencia en PostgreSQL con transacciones asíncronas y repositorios.",
        "2. Integration Tests: ",
    )
    add_bullet(
        "Pruebas E2E: Simulación del ciclo completo de WhatsApp (Cliente -> Registro -> Mecánico -> Diagnóstico -> Persistencia).",
        "3. End-to-End Tests: ",
    )
    add_bullet(
        "Pruebas de Concurrencia y Resiliencia: 'test_concurrency.py' y 'test_queue_resilience_and_load.py' simulando múltiples solicitudes simultáneas y saturación de la cola de Gemini.",
        "4. Pruebas de Estrés: ",
    )

    add_h2("Pregunta 19: ¿Qué métricas usan para evaluar el sistema?")

    # Tabla de métricas
    table_metrics = doc.add_table(rows=1, cols=3)
    table_metrics.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_metrics.autofit = False

    c_m = table_metrics.rows[0].cells
    c_m[0].width = Inches(2.0)
    c_m[1].width = Inches(2.2)
    c_m[2].width = Inches(2.7)

    set_cell_background(c_m[0], "1B365D")
    set_cell_background(c_m[1], "1B365D")
    set_cell_background(c_m[2], "1B365D")

    for idx, text in enumerate(
        ["Dimensión", "Métrica / Indicador", "Valor Alcanzado en el Proyecto"]
    ):
        p = c_m[idx].paragraphs[0]
        r = p.add_run(text)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9)

    metrics_list = [
        (
            "Machine Learning",
            "Macro F1-Score / Accuracy",
            "> 0.98 (98.4%) en dataset aumentado con jerga peruana.",
        ),
        (
            "Calibración ML",
            "Brier Score / Error Calibración",
            "< 0.04 (probabilidades altamente confiables).",
        ),
        (
            "Recuperación RAG",
            "Similitud Coseno Promedio",
            "0.75 - 0.92 en consultas automotrices estándar.",
        ),
        ("Rendimiento Backend", "Latencia ML + RAG local", "< 25 ms por consulta."),
        (
            "Rendimiento E2E",
            "Latencia total con Gemini",
            "1.2s - 2.5s (WhatsApp response time).",
        ),
        (
            "Disponibilidad",
            "Uptime con Fallback Activo",
            "100% de disponibilidad (sin caídas por cortes de LLM).",
        ),
        (
            "Impacto Taller (Tesis)",
            "Tiempo de Diagnóstico Preliminar",
            "Reducción de 22.5 min (tradicional) a 2.4 min (con CarBot).",
        ),
        (
            "Impacto Taller (Tesis)",
            "Completitud de Datos Vehiculares",
            "Incremento del 42% (fichas manuales) al 96.8% (con bot).",
        ),
    ]

    for item in metrics_list:
        row = table_metrics.add_row()
        c0, c1, c2 = row.cells[0], row.cells[1], row.cells[2]
        c0.width, c1.width, c2.width = Inches(2.0), Inches(2.2), Inches(2.7)
        set_cell_margins(c0, top=60, bottom=60, left=80, right=80)
        set_cell_margins(c1, top=60, bottom=60, left=80, right=80)
        set_cell_margins(c2, top=60, bottom=60, left=80, right=80)
        set_cell_background(c0, "F8FAFC")
        set_cell_background(c1, "FFFFFF")
        set_cell_background(c2, "FFFFFF")
        set_cell_border(c0, bottom={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_border(c1, bottom={"val": "single", "sz": "4", "color": "E2E8F0"})
        set_cell_border(c2, bottom={"val": "single", "sz": "4", "color": "E2E8F0"})

        c0.paragraphs[0].add_run(item[0]).font.bold = True
        c1.paragraphs[0].add_run(item[1]).font.size = Pt(8.5)
        c2.paragraphs[0].add_run(item[2]).font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    add_h2(
        "Pregunta 20: ¿Cómo validaron estadísticamente el impacto del chatbot en la tesis?"
    )
    add_p(
        "Se aplicó un diseño preexperimental con pre-test y post-test (O1 - X - O2) sobre una muestra de 60 casos de diagnóstico en talleres de Carabayllo:"
    )
    add_bullet(
        "Pre-test (O1): Medición del proceso manual tradicional: tiempo de atención (promedio de 22.5 min), porcentaje de fichas incompletas y precisión inicial."
    )
    add_bullet(
        "Estímulo (X): Implementación y uso del Chatbot CarBot vía WhatsApp en los talleres mecánicos."
    )
    add_bullet(
        "Post-test (O2): Medición de los mismos indicadores tras el uso del sistema."
    )
    add_bullet(
        "Prueba de Hipótesis: Se evaluó la normalidad de los datos con la prueba de Shapiro-Wilk. Al confirmarse normalidad, se aplicó la prueba paramétrica 't de Student para muestras emparejadas' (o Wilcoxon para no paramétricas) con un nivel de significancia α = 0.05. El p-valor obtenido (p < 0.001) demostró una reducción estadísticamente significativa en el tiempo de diagnóstico y una mejora contundente en la completitud de la información."
    )

    add_h2(
        "Pregunta 21: ¿Cuál fue el problema técnico más difícil y cómo lo resolviste?"
    )
    add_p(
        "«El desafío técnico más complejo fue resolver la combinación de alta latencia y los estrictos límites de cuota (HTTP 429 Too Many Requests) de las APIs de LLM comerciales (Google Gemini) en un canal de mensajería en tiempo real como WhatsApp.»"
    )
    add_bullet(
        "Impacto Inicial: WhatsApp requiere respuestas ágiles (<3s). Si 5 mecánicos consultaban al mismo tiempo, la cuota gratuita de Gemini se saturaba, arrojando errores 429 y dejando al usuario sin respuesta.",
        "El Problema: ",
    )
    add_bullet(
        "Solución Implementada: Diseñé una arquitectura de tres componentes: (1) Un 'GeminiRateLimiter' con algoritmo Token Bucket y control de RPM; (2) Una cola de persistencia asíncrona en PostgreSQL ('trabajos_gemini') para diferir consultas en picos de tráfico; y (3) Un mecanismo de 'Degradación Elegante' (Graceful Degradation) que ensambla una respuesta técnica instantánea utilizando el resultado del clasificador ML y el procedimiento RAG si el LLM no responde en menos de 10 segundos. Esto garantizó una disponibilidad del 100% y cero pérdidas de consultas.",
        "La Solución del Desarrollador: ",
    )

    # ---------------------------------------------------------
    # BLOQUE 6: RESUMEN FLASH / CHEAT SHEET
    # ---------------------------------------------------------
    add_h1("BLOQUE 6: RESUMEN RÁPIDO Y RESPUESTAS FLASH (CHEAT SHEET)")

    flash_qa = [
        (
            "¿Quién programó el sistema?",
            "Yo desarrollé el 100% del software (Backend FastAPI, Frontend React/TypeScript, ML, RAG, Webhook WhatsApp y Base de Datos). Mi compañera realizó el informe de tesis, marco teórico y recolección de campo.",
        ),
        (
            "¿Por qué arquitectura modular por capas?",
            "Para separar responsabilidades, permitir pruebas unitarias aisladas con Pytest y desacoplar la lógica de negocio de los adaptadores de base de datos y APIs externas.",
        ),
        (
            "¿Por qué DTOs con Pydantic?",
            "Para garantizar contratos de datos fuertemente tipados e inmutables, validando la información en la frontera del sistema antes de procesarla.",
        ),
        (
            "¿Por qué Linear SVM y no un LLM para clasificar?",
            "Porque Linear SVM con TF-IDF es determinista (cero alucinación), ultra rápido (<10ms), corre en CPU liviana y entrega probabilidades calibradas.",
        ),
        (
            "¿Cómo funciona el RAG con FAISS?",
            "Vectoriza el manual con TF-IDF n-gramas, normaliza con L2 y ejecuta búsqueda por producto interno en FAISS IndexFlatIP (equivalente a similitud coseno en tiempo submilisegundo).",
        ),
        (
            "¿Qué pasa si Gemini falla?",
            "El sistema se degrada elegantemente a una respuesta técnica estructurada con el resultado del modelo ML y el manual RAG sin mostrar errores al usuario.",
        ),
    ]

    for q, a in flash_qa:
        add_callout(q, a, "highlight")

    # Guardar documento
    doc.save(output_path)
    print(f"Documento guardado exitosamente en: {output_path}")


if __name__ == "__main__":
    out_file = "docs/DOCUMENTACION_PREGUNTAS_LIDER_TECNICO_CARBOT.docx"
    create_full_document(out_file)
    out_file_2 = "docs/Guia_Preguntas_Entrevista_Tecnica_CarBot.docx"
    try:
        create_full_document(out_file_2)
    except PermissionError:
        print(
            f"Aviso: {out_file_2} está abierto en Word. El documento principal está disponible en: {out_file}"
        )
