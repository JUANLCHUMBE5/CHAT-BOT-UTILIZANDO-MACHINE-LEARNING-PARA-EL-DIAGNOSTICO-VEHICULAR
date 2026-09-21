"""
Generador de Documento Word (.docx):
Mapeo de Estructura de CarBot y Auditoría de Preparación para Servidor.
"""

import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_DOCX = "Mapeo_Estructura_y_Auditoria_Servidor_CarBot.docx"

# Paleta de colores profesionales
COLOR_PRIMARY = RGBColor(26, 54, 93)     # Azul Marino Profundo (#1A365D)
COLOR_SECONDARY = RGBColor(43, 108, 176) # Azul Corporativo (#2B6CB0)
COLOR_DARK = RGBColor(45, 55, 72)        # Gris Pizarra Oscuro (#2D3748)
COLOR_MUTED = RGBColor(113, 128, 150)    # Gris Medio (#718096)
COLOR_ALERT = RGBColor(197, 48, 48)      # Rojo Alerta (#C53030)
COLOR_SUCCESS = RGBColor(34, 84, 61)     # Verde Éxito (#22543D)

HEX_PRIMARY = "1A365D"
HEX_SECONDARY = "2B6CB0"
HEX_LIGHT_BG = "F7FAFC"
HEX_ALERT_BG = "FFF5F5"
HEX_ALERT_BORDER = "FEB2B2"
HEX_WARN_BG = "FFFAF0"
HEX_WARN_BORDER = "FEEBC8"
HEX_SUCCESS_BG = "F0FFF4"
HEX_SUCCESS_BORDER = "C6F6D5"
HEX_BORDER_GRAY = "E2E8F0"


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}>'
                      f'<w:top w:w="{top}" w:type="dxa"/>'
                      f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
                      f'<w:left w:w="{left}" w:type="dxa"/>'
                      f'<w:right w:w="{right}" w:type="dxa"/>'
                      f'</w:tcMar>')
    tcPr.append(tcMar)


def set_table_borders(table, color="D2D6DC"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}>'
                        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
                        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color}"/>'
                        f'<w:left w:val="none"/>'
                        f'<w:right w:val="none"/>'
                        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
                        f'<w:insideV w:val="none"/>'
                        f'</w:tblBorders>')
    tblPr.append(borders)


def add_callout(doc, text_list, title="ADVERTENCIA / CONDICIÓN CRÍTICA", box_type="alert"):
    bg = HEX_ALERT_BG if box_type == "alert" else (HEX_WARN_BG if box_type == "warn" else HEX_SUCCESS_BG)
    border_color = HEX_ALERT_BORDER if box_type == "alert" else (HEX_WARN_BORDER if box_type == "warn" else HEX_SUCCESS_BORDER)
    title_color = COLOR_ALERT if box_type == "alert" else (RGBColor(192, 86, 33) if box_type == "warn" else COLOR_SUCCESS)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, bg)
    set_cell_margins(cell, top=160, bottom=160, left=200, right=200)

    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}>'
                        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
                        f'<w:top w:val="none"/>'
                        f'<w:bottom w:val="none"/>'
                        f'<w:right w:val="none"/>'
                        f'</w:tcBorders>')
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run_title = p.add_run(f"⚠️ {title.upper()}" if box_type == "alert" else f"ℹ️ {title.upper()}")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(10.5)
    run_title.font.bold = True
    run_title.font.color.rgb = title_color

    for item in text_list:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_before = Pt(2)
        p2.paragraph_format.space_after = Pt(2)
        run_item = p2.add_run(f"• {item}")
        run_item.font.name = "Calibri"
        run_item.font.size = Pt(10)
        run_item.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def construir_documento():
    doc = Document()

    # Configuración de márgenes estándar (1 pulgada = 2.54 cm)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.header.is_linked_to_previous = False
        hp = section.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("CarBot — Documento Técnico de Arquitectura y Auditoría de Servidor")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_MUTED

    # =========================================================================
    # PORTADA / ENCABEZADO PRINCIPAL
    # =========================================================================
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("CARBOT: MAPEO INTEGRAL DE ARQUITECTURA, COMPONENTES DE SERVIDOR Y AUDITORÍA PREVIA AL DESPLIEGUE")
    run_title.font.name = "Arial"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    run_sub = p_sub.add_run("Informe Técnico Explicativo: Estructura del Sistema, Servicios Contenerizados y Razones Fundamentales por las Cuales el Producto Aún No Debe Lanzarse a Producción")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True
    run_sub.font.color.rgb = COLOR_SECONDARY

    # Ficha de Metadatos
    tbl_meta = doc.add_table(rows=5, cols=2)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_meta)
    meta_data = [
        ("Proyecto / Producto:", "CarBot — Asistente de Diagnóstico Vehicular con Inteligencia Artificial"),
        ("Arquitectura Principal:", "FastAPI (Backend) + React/Vite (Frontend) + PostgreSQL + Redis + Linear SVM/RAG"),
        ("Ambiente Evaluado:", "Contenedores Docker / Servidor Linux-Windows (Ambiente de Desarrollo/Staging)"),
        ("Estado de Madurez:", "NO LISTO PARA PRODUCCIÓN (Fase 10 de ML en curso + Validación de Campo de Tesis pendiente)"),
        ("Fecha del Informe:", "Septiembre 2026 — Documento de Control Técnico y Gobernanza de Despliegue")
    ]
    for i, (k, v) in enumerate(meta_data):
        cell_k = tbl_meta.cell(i, 0)
        cell_v = tbl_meta.cell(i, 1)
        cell_k.width = Inches(2.2)
        cell_v.width = Inches(4.3)
        set_cell_background(cell_k, HEX_LIGHT_BG)
        set_cell_margins(cell_k, 80, 80, 100, 100)
        set_cell_margins(cell_v, 80, 80, 100, 100)

        p_k = cell_k.paragraphs[0]
        r_k = p_k.add_run(k)
        r_k.font.bold = True
        r_k.font.size = Pt(9.5)
        r_k.font.color.rgb = COLOR_PRIMARY

        p_v = cell_v.paragraphs[0]
        r_v = p_v.add_run(v)
        r_v.font.size = Pt(9.5)
        if "NO LISTO" in v:
            r_v.font.bold = True
            r_v.font.color.rgb = COLOR_ALERT

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # =========================================================================
    # SECCIÓN 1: RESUMEN EJECUTIVO (EL POR QUÉ NO LANZAR AÚN)
    # =========================================================================
    p_s1 = doc.add_heading(level=1)
    r = p_s1.add_run("1. Resumen Ejecutivo: ¿Por qué CarBot NO debe desplegarse aún en Producción?")
    r.font.color.rgb = COLOR_PRIMARY

    p = doc.add_paragraph()
    p.add_run("El objetivo de este documento es proporcionar una radiografía transparente y exhaustiva de lo que compone actualmente el repositorio y los servidores de ")
    p.add_run("CarBot").bold = True
    p.add_run(". Ante el interés del equipo o de las partes interesadas de 'subir el producto al servidor ya mismo', es indispensable comunicar formalmente que el software ")
    p.add_run("se encuentra en una etapa intermedia de entrenamiento supervisado y calibración técnica").bold = True
    p.add_run(". Lanzarlo en este momento causaría fallas operativas, costos innecesarios y pondría en riesgo la validez metodológica de la tesis.")

    add_callout(doc, [
        "Fase 10 de Machine Learning Incompleta: El nuevo corpus de entrenamiento estratificado tiene completadas 53 de las 61 clases taxonómicas (Lotes 01 al 09). Faltan los Lotes 10 y 11 (Climatización y Carrocería/Neumática), el reentrenamiento global y el benchmark ciego de validación.",
        "Integridad Académica de la Tesis: El protocolo de investigación prohíbe terminantemente declarar hipótesis aceptadas o abrir la plataforma a producción sin antes registrar y contrastar los 60 casos reales en el taller mecánico con los instrumentos físicos oficiales.",
        "Falta de Credenciales Productivas de Meta WhatsApp: El webhook y los canales de mensajería están configurados para desarrollo/staging. Se requiere el alta formal de números de teléfono empresariales, Webhook Verify Tokens permanentes y plantillas aprobadas por Meta.",
        "Ausencia de Proxy Inverso con SSL/TLS: El backend actualmente expone puertos sin terminación HTTPS segura gestionada por Nginx/Traefik, lo cual es un requisito obligatorio para que los servidores de Meta acepten el webhook.",
        "Riesgo de Bloqueo por Cuotas de Gemini: Sin la activación y monitoreo estricto del modo degradado (Fallback ML+RAG local), una ráfaga de usuarios externos agotaría la cuota de la API de Google, dejando a los mecánicos sin respuesta."
    ], title="4 Razones Críticas por las que el Sistema Aún NO está Listo para Producción", box_type="alert")

    # =========================================================================
    # SECCIÓN 2: MAPEO DE LO QUE CONTIENE EL SERVIDOR (INFRAESTRUCTURA DOCKER)
    # =========================================================================
    p_s2 = doc.add_heading(level=1)
    r = p_s2.add_run("2. Mapeo de Contenedores y Servicios del Servidor (Docker Compose)")
    r.font.color.rgb = COLOR_PRIMARY

    p = doc.add_paragraph()
    p.add_run("El despliegue de CarBot está orquestado mediante ")
    p.add_run("Docker Compose").bold = True
    p.add_run(" en contenedores aislados. A continuación se detalla cada componente que vive dentro del servidor, su rol, su tecnología y sus puertos de comunicación:")

    tbl_serv = doc.add_table(rows=5, cols=5)
    tbl_serv.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_serv)
    headers_serv = ["Servicio / Contenedor", "Tecnología Base", "Puerto Interno / Externo", "Volumen / Persistencia", "Responsabilidad Principal"]
    for j, h in enumerate(headers_serv):
        c = tbl_serv.cell(0, j)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, 100, 100, 120, 120)
        p_h = c.paragraphs[0]
        r_h = p_h.add_run(h)
        r_h.font.bold = True
        r_h.font.size = Pt(9)
        r_h.font.color.rgb = RGBColor(255, 255, 255)

    filas_serv = [
        ("api\n(Backend FastAPI)", "Python 3.12 / FastAPI / Uvicorn", "8000 : 8000\n(HTTP API REST)", "./machine_learning (RO)\nCódigo fuente backend", "Recibe webhooks de WhatsApp, gestiona autenticación JWT, orquesta casos de uso de diagnósticos y expone endpoints de métricas."),
        ("worker\n(Procesador de Colas)", "Python 3.12 / Background Task", "Sin puerto expuesto\n(Consumidor interno)", "./machine_learning (RW)\nAcceso a modelos y RAG", "Procesa en segundo plano las consultas complejas, ejecuta inferencias ML, recupera manuales en FAISS y sintetiza diagnósticos con Gemini."),
        ("postgres\n(Base de Datos Relacional)", "PostgreSQL 17 Alpine", "5432 : 5433\n(Conexión BD)", "carbot_postgres:/var/lib/\npostgresql/data", "Persistencia transaccional de diagnósticos, usuarios, mecánicos, auditorías, tablas pretest/postest y trazabilidad de eventos."),
        ("redis\n(Caché y Cola en Memoria)", "Redis 7 Alpine", "6379 : 6379\n(Memoria volátil)", "carbot_redis:/data\n(AOF persistencia)", "Gestión de limitación de tasa (Rate Limiting), control de concurrencia de cuotas de API externa y candados distribuidos de bloqueo.")
    ]

    for i, fila in enumerate(filas_serv, 1):
        bg = HEX_LIGHT_BG if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(fila):
            c = tbl_serv.cell(i, j)
            set_cell_background(c, bg)
            set_cell_margins(c, 80, 80, 100, 100)
            p_c = c.paragraphs[0]
            r_c = p_c.add_run(val)
            r_c.font.size = Pt(8.5)
            r_c.font.color.rgb = COLOR_DARK
            if j == 0:
                r_c.font.bold = True
                r_c.font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # =========================================================================
    # SECCIÓN 3: MAPEO DE MÓDULOS DE CÓDIGO (CLEAN ARCHITECTURE)
    # =========================================================================
    p_s3 = doc.add_heading(level=1)
    r = p_s3.add_run("3. Mapeo de la Estructura de Código del Repositorio")
    r.font.color.rgb = COLOR_PRIMARY

    p = doc.add_paragraph()
    p.add_run("El repositorio está estructurado bajo principios de ")
    p.add_run("Clean Architecture (Arquitectura Limpia)").bold = True
    p.add_run(" para garantizar desacoplamiento, alta cohesión y testeabilidad:")

    modulos_desc = [
        ("backend/src/domain (o core/diagnostico)", "Reglas de Negocio Puras", "Contiene las entidades del dominio, la taxonomía cerrada de exactamente 61 clases vehiculares y las políticas de fusión diagnóstica. No depende de base de datos ni de frameworks web."),
        ("backend/src/application", "Casos de Uso y Orquestación", "Módulos de coordinación de servicios: `diagnostico_service.py`, `webhook_service.py` (desacoplado en identificador de identidad, validador y persistidor) y jobs en segundo plano (`worker.py`)."),
        ("backend/src/infrastructure", "Adaptadores y Persistencia", "Implementaciones concretas: Repositorios SQLAlchemy de PostgreSQL, clientes de Redis para Rate Limiting, adaptador de WhatsApp Meta Cloud API, cliente de Google Gemini y persistencia de vectorstore FAISS."),
        ("backend/src/interfaces/api", "Contratos HTTP y Controladores", "Endpoints de FastAPI v1: `/auth` (seguridad JWT), `/diagnostico` (consultas y Top 3 diferencial), `/mecanicos` (perfiles de taller), `/validacion-taller` (registro de campo) y `/webhook` (recepción Meta)."),
        ("frontend/src", "Interfaz de Usuario (SPA)", "Cliente React con Vite y TypeScript. Diseñado para monitoreo en taller mecánico, panel de control de diagnósticos, trazabilidad de telemetría y dashboard de métricas de tesis."),
        ("machine_learning", "Pipeline de Inteligencia Artificial", "Almacena los artefactos binarios de ML: Vectorizador TF-IDF, Clasificador Linear SVM multiclase, Clasificador Macro, Índice FAISS RAG de manuales de taller y datasets de entrenamiento (Fase 8.3 y Fase 10).")
    ]

    tbl_mod = doc.add_table(rows=len(modulos_desc)+1, cols=3)
    tbl_mod.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_mod)
    for j, h in enumerate(["Capa / Módulo", "Categoría Arquitectónica", "Descripción y Componentes Clave"]):
        c = tbl_mod.cell(0, j)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, 100, 100, 120, 120)
        p_h = c.paragraphs[0]
        r_h = p_h.add_run(h)
        r_h.font.bold = True
        r_h.font.size = Pt(9)
        r_h.font.color.rgb = RGBColor(255, 255, 255)

    for i, (m, cat, desc) in enumerate(modulos_desc, 1):
        bg = HEX_LIGHT_BG if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate([m, cat, desc]):
            c = tbl_mod.cell(i, j)
            set_cell_background(c, bg)
            set_cell_margins(c, 80, 80, 100, 100)
            p_c = c.paragraphs[0]
            r_c = p_c.add_run(val)
            r_c.font.size = Pt(8.5)
            r_c.font.color.rgb = COLOR_DARK
            if j == 0:
                r_c.font.bold = True
                r_c.font.color.rgb = COLOR_PRIMARY
            elif j == 1:
                r_c.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # =========================================================================
    # SECCIÓN 4: BASE DE DATOS POSTGRESQL (MODELOS Y TABLAS)
    # =========================================================================
    p_s4 = doc.add_heading(level=1)
    r = p_s4.add_run("4. Mapeo de la Base de Datos Relacional (PostgreSQL)")
    r.font.color.rgb = COLOR_PRIMARY

    p = doc.add_paragraph()
    p.add_run("El esquema de base de datos se gestiona mediante migraciones de ")
    p.add_run("Alembic").bold = True
    p.add_run(" y está estructurado en modelos relacionales especializados:")

    tbl_db = doc.add_table(rows=7, cols=3)
    tbl_db.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_db)
    for j, h in enumerate(["Archivo de Modelo", "Entidad / Tabla Principal", "Propósito en el Sistema"]):
        c = tbl_db.cell(0, j)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, 100, 100, 120, 120)
        p_h = c.paragraphs[0]
        r_h = p_h.add_run(h)
        r_h.font.bold = True
        r_h.font.size = Pt(9)
        r_h.font.color.rgb = RGBColor(255, 255, 255)

    filas_db = [
        ("diagnostics.py", "diagnosticos, resultados_ml", "Registra cada consulta, síntoma extraído, código DTC, probabilidades del modelo Linear SVM (Top 1, Top 2, Top 3), recomendación de taller y tiempos de respuesta."),
        ("validation.py", "validaciones_campo_taller", "Tabla de contraste de tesis: registra la confirmación física de la falla en el elevador realizada por el mecánico frente a la predicción emitida por el bot (exactitud real)."),
        ("operations.py", "talleres, mecanicos, vehiculos", "Mapeo multi-inquilino (multi-tenant): aísla los diagnósticos de cada taller, datos de vehículos (marca, modelo, año, VIN) y datos de contacto de los mecánicos."),
        ("jobs.py", "cola_trabajos_gemini", "Gestión de trabajos asíncronos para el worker. Registra estados (`PENDIENTE`, `PROCESANDO`, `COMPLETADO`, `FALLIDO`), reintentos y bloqueos seguros para evitar condiciones de carrera."),
        ("messaging.py", "mensajes_whatsapp, sesiones", "Historial de mensajes bidireccionales, números de teléfono sanitizados, marcas de tiempo de entrega y estado de la sesión conversacional."),
        ("catalogs.py", "catalogo_dtc, sistemas_vehiculares", "Catálogo técnico canónico de los 61 tipos de avería vehicular y códigos estándar OBD-II vinculados a manuales técnicos.")
    ]

    for i, (mod, tab, prop) in enumerate(filas_db, 1):
        bg = HEX_LIGHT_BG if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate([mod, tab, prop]):
            c = tbl_db.cell(i, j)
            set_cell_background(c, bg)
            set_cell_margins(c, 80, 80, 100, 100)
            p_c = c.paragraphs[0]
            r_c = p_c.add_run(val)
            r_c.font.size = Pt(8.5)
            r_c.font.color.rgb = COLOR_DARK
            if j == 0:
                r_c.font.bold = True
                r_c.font.color.rgb = COLOR_PRIMARY

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # =========================================================================
    # SECCIÓN 5: INTELIGENCIA ARTIFICIAL (ML + RAG + GEMINI)
    # =========================================================================
    p_s5 = doc.add_heading(level=1)
    r = p_s5.add_run("5. Mapeo del Núcleo de Inteligencia Artificial")
    r.font.color.rgb = COLOR_PRIMARY

    p = doc.add_paragraph()
    p.add_run("CarBot opera con una arquitectura híbrida de 3 niveles coordinados: ")
    p.add_run("Machine Learning Clásico + RAG Técnico + LLM de Síntesis").bold = True
    p.add_run(". Esta separación es fundamental para entender por qué no se puede desplegar sin completar el entrenamiento:")

    # Lista con viñetas
    p_ml1 = doc.add_paragraph()
    r = p_ml1.add_run("• Nivel 1: Clasificador Machine Learning (Linear SVM + TF-IDF): ")
    r.bold = True
    r.font.color.rgb = COLOR_PRIMARY
    p_ml1.add_run("Es el motor determinista de clasificación. Recibe el texto coloquial o técnico del mecánico, extrae n-gramas mediante TF-IDF y clasifica la probabilidad entre las 61 averías canónicas de la taxonomía. ")
    p_ml1.add_run("Regla estricta de tesis: Se utiliza Linear SVM, nunca Random Forest ni XGBoost.").bold = True

    p_ml2 = doc.add_paragraph()
    r = p_ml2.add_run("• Nivel 2: RAG Técnico (FAISS Vectorstore + Manuales OEM): ")
    r.bold = True
    r.font.color.rgb = COLOR_PRIMARY
    p_ml2.add_run("Corpus documental de manuales de taller de fabricantes originales. Contiene tolerancias eléctricas, voltajes, torques de apriete, diagramas de vacío y procedimientos metrológicos. ")
    p_ml2.add_run("Regla estricta: No contiene quejas de clientes; solo literatura técnica formal.").italic = True

    p_ml3 = doc.add_paragraph()
    r = p_ml3.add_run("• Nivel 3: Síntesis Asistida por LLM (Google Gemini): ")
    r.bold = True
    r.font.color.rgb = COLOR_PRIMARY
    p_ml3.add_run("Toma el Top 3 de probabilidades predicho por el SVM y los fragmentos técnicos de manuales recuperados por FAISS, y genera un reporte estructurado y pedagógico para WhatsApp. ")
    p_ml3.add_run("Si la cuota de Gemini se agota, el sistema entra en Modo Degradado (Fallback ML+RAG puro).").bold = True

    add_callout(doc, [
        "Estado del Modelo en el Servidor: El servidor actual ejecuta los artefactos de la FASE 8.3 (19 artefactos congelados e inmutables).",
        "Fase 10 en Desarrollo: Se están construyendo los lotes estratificados L1/L2/L3. De las 61 clases, se tienen 53 clases consolidadas en dataset_fase10_master.csv (2120 registros).",
        "Entrenar y desplegar el nuevo modelo requiere finalizar los Lotes 10 y 11, ejecutar la validación ciega de 100 casos y asegurar que supera el baseline de 8.3 sin regresiones."
    ], title="Estado de la Capa de Machine Learning", box_type="warn")

    # =========================================================================
    # SECCIÓN 6: CHECKLIST TÉCNICO PARA EL LANZAMIENTO A SERVIDOR
    # =========================================================================
    p_s6 = doc.add_heading(level=1)
    r = p_s6.add_run("6. Checklist y Requisitos Técnicos Previos al Lanzamiento Oficial")
    r.font.color.rgb = COLOR_PRIMARY

    p = doc.add_paragraph()
    p.add_run("Para que el despliegue al servidor de producción sea seguro, estable y metodológicamente irreprochable, se debe cumplir obligatoriamente la siguiente lista de verificación:")

    tbl_chk = doc.add_table(rows=7, cols=4)
    tbl_chk.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl_chk)
    headers_chk = ["Fase / Área", "Requisito Técnico", "Estado Actual", "Impacto si se Ignora"]
    for j, h in enumerate(headers_chk):
        c = tbl_chk.cell(0, j)
        set_cell_background(c, HEX_PRIMARY)
        set_cell_margins(c, 100, 100, 120, 120)
        p_h = c.paragraphs[0]
        r_h = p_h.add_run(h)
        r_h.font.bold = True
        r_h.font.size = Pt(9)
        r_h.font.color.rgb = RGBColor(255, 255, 255)

    filas_chk = [
        ("Machine Learning", "Completar Lotes 10 y 11 (Clases 54 a 61) y reentrenar modelo", "🟡 En Construcción (53/61)", "El modelo quedaría sin cobertura para aire acondicionado, elevalunas y frenos de aire."),
        ("Metodología Tesis", "Aplicar instrumentos con los 60 casos reales de mecánicos en taller", "🔴 Pendiente de Campo", "Invalidez académica: los resultados no tendrían validez científica ante jurados."),
        ("Infraestructura Web", "Configurar Nginx inverso con certificados SSL/TLS (Let's Encrypt)", "🔴 Pendiente en Servidor", "Meta WhatsApp rechazará la conexión del webhook por falta de HTTPS seguro."),
        ("Variables Entorno", "Definir POSTGRES_PASSWORD segura y credenciales permanentes de Meta", "🟡 Usando .env local", "Vulnerabilidad de seguridad grave en el servidor de base de datos."),
        ("Worker & Resiliencia", "Validar Rate Limiting y auto-reinicio del contenedor worker", "🟢 Funcional en Docker", "Si el worker se detiene, los mensajes de WhatsApp quedan sin respuesta."),
        ("Frontend Vite", "Compilar bundle estático para producción (`npm run build`)", "🟡 Modo dev local", "Rendimiento deficiente y saturación de memoria si se sirve con Vite Dev Server.")
    ]

    for i, (area, req, est, imp) in enumerate(filas_chk, 1):
        bg = HEX_LIGHT_BG if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate([area, req, est, imp]):
            c = tbl_chk.cell(i, j)
            set_cell_background(c, bg)
            set_cell_margins(c, 80, 80, 100, 100)
            p_c = c.paragraphs[0]
            r_c = p_c.add_run(val)
            r_c.font.size = Pt(8.5)
            r_c.font.color.rgb = COLOR_DARK
            if j == 0:
                r_c.font.bold = True
                r_c.font.color.rgb = COLOR_PRIMARY
            elif j == 2:
                r_c.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # =========================================================================
    # SECCIÓN 7: CONCLUSIÓN Y RECOMENDACIÓN FORMAL
    # =========================================================================
    p_s7 = doc.add_heading(level=1)
    r = p_s7.add_run("7. Dictamen Final y Recomendación de Acción")
    r.font.color.rgb = COLOR_PRIMARY

    p_concl = doc.add_paragraph()
    p_concl.add_run("CarBot cuenta con una arquitectura de software robusta, moderna y bien delimitada en sus capas de backend, base de datos y worker asíncrono. Sin embargo, ")
    p_concl.add_run("NO es recomendable abrir el servidor al público o a usuarios reales en este momento").bold = True
    p_concl.add_run(". El despliegue prematuro expondría un modelo de machine learning en plena fase de expansión y violaría los principios metodológicos de la investigación.")

    p_rec = doc.add_paragraph()
    p_rec.add_run("Recomendación Inmediata: ").bold = True
    p_rec.add_run("Mantener el servidor en entorno cerrado de pruebas (Staging / Red Local), completar los Lotes 10 y 11 de la Fase 10, ejecutar la compilación de producción del frontend, asegurar el proxy Nginx con SSL y programar la recolección oficial de los 60 casos de taller de la tesis.")

    # Guardar documento
    doc.save(OUTPUT_DOCX)
    print(f"[EXITO] Documento Word generado en: {os.path.abspath(OUTPUT_DOCX)}")


if __name__ == "__main__":
    construir_documento()
