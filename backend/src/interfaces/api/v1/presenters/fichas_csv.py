"""Exportación del Anexo 2; la distribución de muestra requiere aprobación humana."""

import csv
import io
from datetime import date
from typing import Any


def _sanitizar_campo_csv(val: Any) -> str:
    """Neutraliza posibles fórmulas maliciosas de hojas de cálculo (=, +, -, @, tab, retorno)."""
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


def construir_fichas_csv(
    registros: list[dict], fecha_desde: date | None, fecha_hasta: date | None
) -> io.StringIO:
    total_casos = len(registros)
    pre_count = sum(1 for r in registros if str(r.get("tipo_registro")) == "THESIS_PRETEST")
    post_count = sum(1 for r in registros if str(r.get("tipo_registro")) == "THESIS_POSTTEST")
    estado_muestra = "DISTRIBUCIÓN PRE/POST PENDIENTE DE CONFIRMACIÓN DEL ASESOR"

    output = io.StringIO()
    output.write(
        "# =================================================================================================\n"
    )
    output.write("# UNIVERSIDAD CÉSAR VALLEJO - ESCUELA DE INGENIERÍA DE SISTEMAS\n")
    output.write(
        "# TESIS: CHATBOT UTILIZANDO MACHINE LEARNING PARA EL DIAGNÓSTICO VEHICULAR (CARTER MOTOR'S E.I.R.L.)\n"
    )
    output.write("# ANEXO 2: MATRIZ DE RECOLECCIÓN DE DATOS EXPERIMENTALES (PRETEST Y POSTEST)\n")
    output.write(
        "# =================================================================================================\n"
    )
    output.write(f"# Total casos verificados exportados: {total_casos}\n")
    output.write(f"# Registros oficiales PRE-TEST: {pre_count}; POST-TEST: {post_count}\n")
    output.write(f"# Periodo evaluado: {fecha_desde or 'Histórico'} a {fecha_hasta or 'Actualidad'}\n")
    output.write(f"# Estado de la muestra oficial: {estado_muestra}\n")
    output.write(
        "# NOTA METODOLÓGICA: El contraste de hipótesis inferencial (pretest vs. postest) queda estrictamente\n"
    )
    output.write(
        "# pendiente de definición con el asesor estadístico según la distribución y naturaleza de la muestra.\n"
    )
    output.write(
        "# Se prohíbe el uso de datos sintéticos o valores simulados para conclusiones formales de la tesis.\n"
    )
    output.write(
        "# =================================================================================================\n"
    )

    columnas_export = [
        "Item",
        "Fase",
        "Tipo_Registro",
        "Fecha",
        "Placa_Enmascarada",
        "Marca_Modelo",
        "Sintoma_Reportado",
        "Descripcion_Sintoma",
        "Vehiculo_Anio",
        "Vehiculo_Kilometraje",
        "Vehiculo_Combustible",
        "Vehiculo_Transmision",
        "Falla_Confirmada_Fisica",
        "Diagnostico_Preliminar_Sin_Chatbot",
        "Falla_Sugerida_Chatbot",
        "Prediccion_Linear_SVM",
        "PPCF_Ficha1_Prediccion_Correcta",
        "PRDC_Ficha2_Campos_Completos",
        "Ficha2_Cantidad_Campos_Completos",
        "Ficha2_Campo1_Codigo_Registro",
        "Ficha2_Campo2_Fecha_Atencion",
        "Ficha2_Campo3_Datos_Generales_Vehiculo",
        "Ficha2_Campo4_Sintomas_Reportados",
        "Ficha2_Campo5_Descripcion_Sintoma",
        "Ficha2_Campo6_Sistema_Afectado_Probable",
        "Ficha2_Campo7_Diagnostico_Confirmado",
        "Ficha2_Campo8_Tiempo_Atencion_Registrado",
        "TPRD_Ficha3_Tiempo_Minutos",
        "Ind1_Sintoma_Validado",
        "Ind2_Procesamiento_Validado",
        "Metodo_Confirmacion",
        "Evidencia_Referencia",
        "Validador_ID",
        "Fecha_Validacion",
        "Estado_Registro",
    ]

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(columnas_export)

    for r in registros:
        detalles = r.get("detalles_campos") if isinstance(r.get("detalles_campos"), dict) else {}

        def campo_completo(clave: str) -> str:
            campo = detalles.get(clave) if isinstance(detalles.get(clave), dict) else {}
            if not campo or "completo" not in campo:
                return ""
            return "1" if campo.get("completo") else "0"

        es_pretest = str(r.get("fase", "")).strip().casefold() in {"pre-test", "pretest"}
        diagnostico_preliminar = r.get("chatbot_prediccion", "") if es_pretest else ""
        falla_sugerida = r.get("chatbot_prediccion", "") if not es_pretest else ""

        fila = [
            _sanitizar_campo_csv(r.get("item", "")),
            _sanitizar_campo_csv(r.get("fase", "")),
            _sanitizar_campo_csv(r.get("tipo_registro", "")),
            _sanitizar_campo_csv(r.get("fecha", "")),
            _sanitizar_campo_csv(r.get("placa_enmascarada", "")),
            _sanitizar_campo_csv(r.get("marca_modelo", "")),
            _sanitizar_campo_csv(r.get("sintoma", "")),
            _sanitizar_campo_csv(r.get("descripcion_sintoma", "")),
            _sanitizar_campo_csv(r.get("vehiculo_anio", "")),
            _sanitizar_campo_csv(r.get("vehiculo_kilometraje", "")),
            _sanitizar_campo_csv(r.get("vehiculo_combustible", "")),
            _sanitizar_campo_csv(r.get("vehiculo_transmision", "")),
            _sanitizar_campo_csv(r.get("falla_real", "")),
            _sanitizar_campo_csv(diagnostico_preliminar),
            _sanitizar_campo_csv(falla_sugerida),
            _sanitizar_campo_csv(falla_sugerida if not es_pretest else ""),
            _sanitizar_campo_csv(r.get("prediccion_correcta", "")),
            _sanitizar_campo_csv(r.get("campos_completos", "")),
            _sanitizar_campo_csv(r.get("cantidad_campos_completos", 0)),
            _sanitizar_campo_csv(campo_completo("campo_1")),
            _sanitizar_campo_csv(campo_completo("campo_2")),
            _sanitizar_campo_csv(campo_completo("campo_3")),
            _sanitizar_campo_csv(campo_completo("campo_4")),
            _sanitizar_campo_csv(campo_completo("campo_5")),
            _sanitizar_campo_csv(campo_completo("campo_6")),
            _sanitizar_campo_csv(campo_completo("campo_7")),
            _sanitizar_campo_csv(campo_completo("campo_8")),
            _sanitizar_campo_csv(r.get("tiempo_diagnostico_minutos", "")),
            _sanitizar_campo_csv(r.get("sintoma_registrado_correctamente", "")),
            _sanitizar_campo_csv(r.get("procesamiento_validado", "")),
            _sanitizar_campo_csv(r.get("metodo_confirmacion", "")),
            _sanitizar_campo_csv(r.get("evidencia_ref", "")),
            _sanitizar_campo_csv(r.get("validado_por_id", "") or r.get("mecanico_id", "")),
            _sanitizar_campo_csv(r.get("fecha_validacion", "")),
            _sanitizar_campo_csv(r.get("estado_registro", "")),
        ]
        writer.writerow(fila)

    output.seek(0)

    return output
